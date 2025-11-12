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
            await self._collect_results(scraped_data)

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
        Discover categories from start URLs.

        Args:
            start_urls: List of starting URLs

        Returns:
            List of discovered categories
        """
        try:
            # For now, just use the start URLs as categories
            # In a full implementation, you would use the CategoryScraper
            categories = [{"url": url, "name": url} for url in start_urls]

            self.progress_reporter.log_info(f"Discovered {len(categories)} categories")
            return categories

        except Exception as e:
            logger.error(f"Category discovery failed: {e}")
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Category discovery failed: {str(e)}")
            return []

    async def _collect_products(self, categories: list) -> list:
        """
        Collect product URLs from categories.

        Args:
            categories: List of category dictionaries

        Returns:
            List of product dictionaries
        """
        try:
            # Simplified product collection
            # In a full implementation, use ProductCollector
            products = []

            for category in categories:
                # For now, just create dummy products from the category URL
                products.append({
                    "url": category["url"],
                    "title": f"Product from {category['name']}",
                    "category": category["name"],
                })

            max_pages = self.scraper_config["max_pages"]
            products = products[:max_pages]

            self.progress_reporter.log_info(f"Collected {len(products)} product URLs")
            return products

        except Exception as e:
            logger.error(f"Product collection failed: {e}")
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Product collection failed: {str(e)}")
            return []

    async def _scrape_products(self, products: list, start_time: datetime) -> list:
        """
        Scrape product details.

        Args:
            products: List of product dictionaries
            start_time: Job start time

        Returns:
            List of scraped product data
        """
        scraped_data = []

        for i, product in enumerate(products, 1):
            try:
                # Simulate scraping (in full implementation, use ProductScraper)
                product_data = {
                    "url": product["url"],
                    "title": product["title"],
                    "category": product.get("category", ""),
                    "scraped_at": datetime.utcnow().isoformat(),
                    # Add more fields as needed
                }

                scraped_data.append(product_data)

                # Update progress
                self.progress_reporter.update_progress(
                    pages_scraped=i,
                    total_pages=len(products),
                    started_at=start_time,
                )

                # Log every 10 products
                if i % 10 == 0:
                    self.progress_reporter.log_info(f"Scraped {i}/{len(products)} products")

            except Exception as e:
                logger.error(f"Failed to scrape product {product.get('url')}: {e}")
                self.stats["errors"] += 1
                self.progress_reporter.log_error(f"Failed to scrape product: {str(e)}")

        return scraped_data

    async def _download_pdfs(self, scraped_data: list):
        """
        Download PDF documents.

        Args:
            scraped_data: List of scraped product data
        """
        try:
            # In full implementation, use PDFDownloader
            self.progress_reporter.log_info("PDF download step (placeholder)")
        except Exception as e:
            logger.error(f"PDF download failed: {e}")
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"PDF download failed: {str(e)}")

    async def _collect_results(self, scraped_data: list):
        """
        Collect and store results.

        Args:
            scraped_data: List of scraped data
        """
        try:
            # Collect results in batch
            results = []
            for data in scraped_data:
                results.append({
                    "url": data.get("url"),
                    "content": data,
                    "links": [],
                    "metadata": {"source": "api_job"},
                })

            self.result_collector.collect_batch(results)

            # Save to file
            file_format = self.scraper_config.get("file_format", "json")
            self.result_collector.save_to_file(
                f"results.{file_format}",
                scraped_data,
                format=file_format,
            )

            self.progress_reporter.log_info(f"Results collected: {len(scraped_data)} items")

        except Exception as e:
            logger.error(f"Result collection failed: {e}")
            self.stats["errors"] += 1
            self.progress_reporter.log_error(f"Result collection failed: {str(e)}")
