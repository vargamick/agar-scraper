"""
Scraper adapter.

Adapts existing scraper modules to work with the API job system.
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from uuid import UUID

from api.database.models import JobStatus, LogLevel
from api.scraper.config_builder import ConfigBuilder
from api.scraper.progress_reporter import ProgressReporter
from api.scraper.result_collector import ResultCollector

# Import existing scraper modules
from core.category_scraper import CategoryScraper
from core.product_collector import ProductCollector
from core.product_scraper import ProductScraper
from core.pdf_downloader import PDFDownloader

logger = logging.getLogger(__name__)


class ScraperAdapter:
    """
    Adapts existing scraper code to work with the API job system.

    Runs the existing scraper modules and reports progress back to the API.
    """

    def __init__(
        self,
        job_id: UUID,
        job_config: Dict[str, Any],
        output_config: Dict[str, Any],
    ):
        """
        Initialize scraper adapter.

        Args:
            job_id: Job UUID
            job_config: Job configuration dictionary
            output_config: Output configuration dictionary
        """
        self.job_id = job_id
        self.config_builder = ConfigBuilder(job_id, job_config, output_config)
        self.progress_reporter = ProgressReporter(job_id)
        self.output_path = self.config_builder.get_output_path()
        self.result_collector = ResultCollector(job_id, self.output_path)

        # Scraper configuration
        self.scraper_config = self.config_builder.build_scraper_config()

        # Statistics
        self.stats = {
            "bytes_downloaded": 0,
            "items_extracted": 0,
            "errors": 0,
            "retries": 0,
        }

    async def execute(self):
        """
        Execute the scraper job.

        This is the main entry point that runs the complete scraping pipeline.
        """
        start_time = datetime.utcnow()

        try:
            # Update status to running
            self.progress_reporter.update_status(JobStatus.RUNNING)
            self.progress_reporter.log_info("Scraper job started")

            # Get configuration
            start_urls = self.scraper_config["start_urls"]
            max_pages = self.scraper_config["max_pages"]

            # Initialize progress
            self.progress_reporter.update_progress(
                pages_scraped=0,
                total_pages=max_pages,
                started_at=start_time,
            )

            # Step 1: Discover categories (for web scraping)
            self.progress_reporter.log_info("Discovering categories")
            categories = await self._discover_categories(start_urls)

            # Step 2: Collect product URLs
            self.progress_reporter.log_info(f"Collecting products from {len(categories)} categories")
            products = await self._collect_products(categories)

            # Update progress
            total_products = len(products)
            self.progress_reporter.update_progress(
                pages_scraped=0,
                total_pages=min(total_products, max_pages),
                started_at=start_time,
            )

            # Step 3: Scrape product details
            self.progress_reporter.log_info(f"Scraping {total_products} products")
            scraped_data = await self._scrape_products(products, start_time)

            # Step 4: Download PDFs (if applicable)
            if scraped_data:
                self.progress_reporter.log_info("Downloading PDF documents")
                await self._download_pdfs(scraped_data)

            # Step 5: Collect results
            self.progress_reporter.log_info("Collecting results")
            await self._collect_results(scraped_data, categories, products)

            # Update final statistics
            self.stats["items_extracted"] = len(scraped_data)
            self.progress_reporter.update_stats(**self.stats)

            # Mark as completed
            self.progress_reporter.update_status(JobStatus.COMPLETED)
            self.progress_reporter.log_info(f"Scraper job completed successfully. {len(scraped_data)} items extracted.")

        except Exception as e:
            logger.error(f"Scraper job failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.update_stats(**self.stats)
            self.progress_reporter.update_status(JobStatus.FAILED)
            self.progress_reporter.log_error(f"Scraper job failed: {str(e)}")
            raise

        finally:
            # Cleanup
            self.progress_reporter.close()
            self.result_collector.close()

    async def _discover_categories(self, start_urls: list) -> list:
        """
        Discover categories from start URLs using CategoryScraper.

        Args:
            start_urls: List of starting URLs

        Returns:
            List of discovered categories

        Raises:
            Exception: If category discovery fails
        """
        try:
            from config.config_loader import ConfigLoader
            from pathlib import Path

            # Load client configuration
            client_name = self.scraper_config.get("client_name", "agar")
            config = ConfigLoader.load_client_config(client_name)

            # Initialize CategoryScraper
            category_scraper = CategoryScraper(
                config=config,
                output_dir=Path(self.output_path),
                test_mode=self.scraper_config.get("test_mode", False)
            )

            # Discover categories from the website
            categories = await category_scraper.discover_categories()

            if not categories:
                raise ValueError("No categories discovered from website")

            self.progress_reporter.log_info(f"Discovered {len(categories)} categories")
            return categories

        except Exception as e:
            logger.error(f"Category discovery failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Category discovery failed: {str(e)}")
            raise

    async def _collect_products(self, categories: list) -> list:
        """
        Collect product URLs from categories using ProductCollector.

        Args:
            categories: List of category dictionaries

        Returns:
            List of product dictionaries

        Raises:
            Exception: If product collection fails
        """
        try:
            from config.config_loader import ConfigLoader
            from pathlib import Path

            # Load client configuration
            client_name = self.scraper_config.get("client_name", "agar")
            config = ConfigLoader.load_client_config(client_name)

            # Initialize ProductCollector
            product_collector = ProductCollector(
                config=config,
                output_dir=Path(self.output_path),
                test_mode=self.scraper_config.get("test_mode", False)
            )

            # Collect products from all categories
            products = await product_collector.collect_all_products(categories)

            if not products:
                raise ValueError("No products collected from categories")

            # Apply max_pages limit
            max_pages = self.scraper_config.get("max_pages", len(products))
            if len(products) > max_pages:
                products = products[:max_pages]
                self.progress_reporter.log_info(f"Limited to {max_pages} products")

            self.progress_reporter.log_info(f"Collected {len(products)} product URLs")
            return products

        except Exception as e:
            logger.error(f"Product collection failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Product collection failed: {str(e)}")
            raise

    async def _scrape_products(self, products: list, start_time: datetime) -> list:
        """
        Scrape product details using ProductScraper.

        Args:
            products: List of product dictionaries
            start_time: Job start time

        Returns:
            List of scraped product data

        Raises:
            Exception: If scraping fails completely
        """
        try:
            from config.config_loader import ConfigLoader
            from pathlib import Path
            from core.product_pdf_scraper import ProductPDFScraper

            # Load client configuration and strategies
            client_name = self.scraper_config.get("client_name", "agar")
            config = ConfigLoader.load_client_config(client_name)
            strategies = ConfigLoader.load_client_strategies(client_name)

            if strategies is None:
                raise ValueError(f"No extraction strategies found for client '{client_name}'")

            # Initialize ProductScraper
            product_scraper = ProductScraper(
                config=config,
                extraction_strategy=strategies,
                output_dir=Path(self.output_path),
                save_screenshots=self.scraper_config.get("save_screenshots", True)
            )

            # Initialize ProductPDFScraper for extracting PDF links
            pdf_scraper = ProductPDFScraper(
                config=config,
                output_dir=Path(self.output_path)
            )

            scraped_data = []
            failed_products = []

            for i, product in enumerate(products, 1):
                try:
                    # Scrape product details
                    product_data = await product_scraper.scrape_product(product)

                    if product_data:
                        # Extract PDF links and add to product data
                        try:
                            pdf_data = await pdf_scraper.scrape_pdf_links(
                                product_url=product_data.get("product_url"),
                                product_name=product_data.get("product_name", "Product")
                            )
                            if pdf_data:
                                product_data.update(pdf_data)
                        except Exception as pdf_error:
                            logger.warning(f"Failed to extract PDF links for {product_data.get('product_name')}: {pdf_error}")
                            # Add empty PDF fields so structure is consistent
                            product_data.update({
                                "sds_url": None,
                                "pds_url": None,
                                "pdf_extraction_method": "failed",
                                "total_pdfs_found": 0
                            })

                        scraped_data.append(product_data)
                    else:
                        failed_products.append(product.get("url", "unknown"))
                        self.stats["errors"] += 1

                    # Update progress
                    self.progress_reporter.update_progress(
                        pages_scraped=i,
                        total_pages=len(products),
                        started_at=start_time,
                    )

                    # Log every 10 products
                    if i % 10 == 0:
                        self.progress_reporter.log_info(
                            f"Scraped {i}/{len(products)} products ({len(scraped_data)} successful, {len(failed_products)} failed)"
                        )

                    # Rate limiting
                    if i < len(products):
                        await asyncio.sleep(config.RATE_LIMIT_DELAY)

                except Exception as e:
                    logger.error(f"Failed to scrape product {product.get('url')}: {e}", exc_info=True)
                    failed_products.append(product.get("url", "unknown"))
                    self.stats["errors"] += 1
                    self.progress_reporter.log_error(f"Failed to scrape product: {str(e)}")

            # Log final statistics
            self.progress_reporter.log_info(
                f"Product scraping complete: {len(scraped_data)} successful, {len(failed_products)} failed"
            )

            if failed_products:
                self.progress_reporter.log_warning(
                    f"Failed products: {', '.join(failed_products[:5])}" +
                    (f"... and {len(failed_products) - 5} more" if len(failed_products) > 5 else "")
                )

            return scraped_data

        except Exception as e:
            logger.error(f"Product scraping failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Product scraping failed: {str(e)}")
            raise

    async def _download_pdfs(self, scraped_data: list):
        """
        Download PDF documents using PDFDownloader.

        Args:
            scraped_data: List of scraped product data

        Raises:
            Exception: If PDF download fails
        """
        try:
            from config.config_loader import ConfigLoader

            # Load client configuration
            client_name = self.scraper_config.get("client_name", "agar")
            config = ConfigLoader.load_client_config(client_name)

            # Initialize PDFDownloader
            pdf_downloader = PDFDownloader(
                config=config,
                run_dir=self.output_path,
                max_retries=3,
                timeout=30
            )

            # Download all PDFs
            stats = await pdf_downloader.download_all_pdfs(products=scraped_data)

            # Update statistics
            self.stats["bytes_downloaded"] = stats.get("total_size_bytes", 0)

            self.progress_reporter.log_info(
                f"PDF download complete: {stats.get('successful_downloads', 0)} successful, "
                f"{stats.get('failed_downloads', 0)} failed, {stats.get('skipped', 0)} skipped"
            )

        except Exception as e:
            logger.error(f"PDF download failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"PDF download failed: {str(e)}")
            raise

    async def _collect_results(self, scraped_data: list, categories: list = None, products: list = None):
        """
        Collect and store results.

        Args:
            scraped_data: List of scraped data
            categories: List of category data (optional)
            products: List of product URL data (optional)

        Raises:
            Exception: If result collection fails
        """
        try:
            import json

            # Collect results in batch
            results = []
            for data in scraped_data:
                results.append({
                    "url": data.get("product_url", data.get("url")),
                    "content": data,
                    "links": [data.get("sds_url"), data.get("pds_url")] if (data.get("sds_url") or data.get("pds_url")) else [],
                    "metadata": {
                        "source": "api_job",
                        "job_id": str(self.job_id),
                        "client_name": self.scraper_config.get("client_name", "unknown")
                    },
                })

            self.result_collector.collect_batch(results)

            # Save to file
            file_format = self.scraper_config.get("file_format", "json")
            self.result_collector.save_to_file(
                f"results.{file_format}",
                scraped_data,
                format=file_format,
            )

            # Save consolidated output files (matching CLI behavior)
            output_dir = Path(self.output_path)

            # Save categories.json
            if categories:
                categories_file = output_dir / "categories.json"
                with open(categories_file, 'w', encoding='utf-8') as f:
                    json.dump(categories, f, indent=2, ensure_ascii=False)
                self.progress_reporter.log_info(f"Saved categories.json with {len(categories)} categories")

            # Save all_products.json (full product data with PDF metadata)
            if scraped_data:
                all_products_file = output_dir / "all_products.json"
                with open(all_products_file, 'w', encoding='utf-8') as f:
                    json.dump(scraped_data, f, indent=2, ensure_ascii=False)
                self.progress_reporter.log_info(f"Saved all_products.json with {len(scraped_data)} products")

            self.progress_reporter.log_info(f"Results collected: {len(scraped_data)} items")

        except Exception as e:
            logger.error(f"Result collection failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Result collection failed: {str(e)}")
            raise
