"""
Result collector for scraper jobs.

Collects and stores scraped results in the database.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from api.database.connection import get_db_session
from api.database.repositories import JobRepository
from api.database.models import JobResult

logger = logging.getLogger(__name__)


class ResultCollector:
    """
    Collects and stores scraper results.

    Saves results to both database and files.
    """

    def __init__(self, job_id: UUID, output_path: str):
        """
        Initialize result collector.

        Args:
            job_id: Job UUID
            output_path: Output directory path
        """
        self.job_id = job_id
        self.output_path = Path(output_path)
        self._db: Optional[Session] = None
        self._repo: Optional[JobRepository] = None

        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

    def _get_repository(self) -> JobRepository:
        """Get job repository with database session."""
        if self._repo is None:
            self._db = get_db_session()
            self._repo = JobRepository(self._db)
        return self._repo

    def close(self):
        """Close database session."""
        if self._db:
            self._db.close()
            self._db = None
            self._repo = None

    def collect_result(
        self,
        url: str,
        content: Dict[str, Any],
        links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Collect a single result.

        Args:
            url: Scraped URL
            content: Scraped content
            links: Extracted links
            metadata: Additional metadata

        Raises:
            Exception: If result collection fails
        """
        try:
            # Create result record
            result = JobResult(
                job_id=self.job_id,
                url=url,
                scraped_at=datetime.utcnow(),
                content=content,
                links=links or [],
                result_metadata=metadata or {},
            )

            # Save to database
            repo = self._get_repository()
            repo.add_result(result)
            self._db.commit()

            logger.debug(f"Result collected for job {self.job_id}: {url}")
        except Exception as e:
            logger.exception(f"Failed to collect result for job {self.job_id}, url: {url}")
            if self._db:
                self._db.rollback()
            raise

    def collect_batch(self, results: List[Dict[str, Any]]):
        """
        Collect multiple results in batch.

        Args:
            results: List of result dictionaries

        Raises:
            Exception: If batch collection fails
        """
        try:
            repo = self._get_repository()

            for result_data in results:
                result = JobResult(
                    job_id=self.job_id,
                    url=result_data.get("url"),
                    scraped_at=datetime.utcnow(),
                    content=result_data.get("content", {}),
                    links=result_data.get("links", []),
                    result_metadata=result_data.get("metadata", {}),
                )
                repo.add_result(result)

            self._db.commit()
            logger.info(f"Batch of {len(results)} results collected for job {self.job_id}")
        except Exception as e:
            logger.exception(f"Failed to collect batch for job {self.job_id}")
            if self._db:
                self._db.rollback()
            raise

    def save_to_file(self, filename: str, data: Any, format: str = "json"):
        """
        Save data to file.

        Args:
            filename: Output filename
            data: Data to save
            format: File format (json, markdown, html)

        Raises:
            Exception: If file save fails
        """
        try:
            file_path = self.output_path / filename

            if format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
            elif format == "markdown":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._to_markdown(data))
            elif format == "html":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._to_html(data))
            else:
                logger.warning(f"Unknown format: {format}, defaulting to JSON")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)

            logger.debug(f"Data saved to {file_path}")
        except Exception as e:
            logger.exception(f"Failed to save file {filename} for job {self.job_id}")
            raise

    def load_from_scraper_output(self, scraper_output_dir: Path):
        """
        Load results from existing scraper output directory.

        Args:
            scraper_output_dir: Path to scraper output directory
        """
        try:
            # Load products from products directory
            products_dir = scraper_output_dir / "products"
            if products_dir.exists():
                for product_file in products_dir.glob("*.json"):
                    try:
                        with open(product_file, "r", encoding="utf-8") as f:
                            product_data = json.load(f)

                        self.collect_result(
                            url=product_data.get("product_url", ""),
                            content=product_data,
                            links=[],
                            metadata={"source": "scraper_output"},
                        )
                    except Exception as e:
                        logger.error(f"Failed to load product {product_file}: {e}")

            # Load merged data if available
            merged_file = scraper_output_dir / "all_products_data.json"
            if merged_file.exists():
                self.save_to_file("all_products_data.json", json.load(open(merged_file)))

            logger.info(f"Loaded results from {scraper_output_dir}")
        except Exception as e:
            logger.error(f"Failed to load from scraper output: {e}")

    @staticmethod
    def _to_markdown(data: Any) -> str:
        """
        Convert data to markdown format.

        Args:
            data: Data to convert

        Returns:
            Markdown string
        """
        if isinstance(data, dict):
            lines = ["# Scraped Data\n"]
            for key, value in data.items():
                lines.append(f"## {key}\n")
                if isinstance(value, (dict, list)):
                    lines.append(f"```json\n{json.dumps(value, indent=2)}\n```\n")
                else:
                    lines.append(f"{value}\n")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = ["# Scraped Data\n"]
            for i, item in enumerate(data, 1):
                lines.append(f"## Item {i}\n")
                lines.append(f"```json\n{json.dumps(item, indent=2)}\n```\n")
            return "\n".join(lines)
        else:
            return str(data)

    @staticmethod
    def _to_html(data: Any) -> str:
        """
        Convert data to HTML format.

        Args:
            data: Data to convert

        Returns:
            HTML string
        """
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Scraped Data</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Scraped Data</h1>
    <pre>{}</pre>
</body>
</html>
""".format(json.dumps(data, indent=2, default=str))
        return html
