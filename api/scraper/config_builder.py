"""
Configuration builder for scraper jobs.

Converts API job configuration to scraper-compatible configuration.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from api.schemas.job import JobConfig, OutputConfig
from config.base_config import BaseConfig

logger = logging.getLogger(__name__)


class ConfigBuilder:
    """
    Builds scraper configuration from API job config.

    Converts API job configuration format to the format expected
    by the existing scraper modules.
    """

    def __init__(self, job_id: UUID, job_config: Dict[str, Any], output_config: Dict[str, Any]):
        """
        Initialize config builder.

        Args:
            job_id: Job UUID
            job_config: Job configuration dictionary
            output_config: Output configuration dictionary
        """
        self.job_id = job_id
        self.job_config = job_config
        self.output_config = output_config

    def build_scraper_config(self) -> Dict[str, Any]:
        """
        Build configuration for the scraper.

        Returns:
            Configuration dictionary compatible with existing scrapers
        """
        # Extract start URLs
        start_urls = self.job_config.get("startUrls", [])

        # Extract rate limit settings
        rate_limit = self.job_config.get("rateLimit", {})
        rate_limit_min = 1
        rate_limit_max = 3

        if rate_limit:
            requests = rate_limit.get("requests", 10)
            per = rate_limit.get("per", "second")
            # Convert to delay range
            if per == "second":
                rate_limit_min = 1.0 / requests
                rate_limit_max = 2.0 / requests

        # Build base configuration
        config = {
            # Job identification
            "job_id": str(self.job_id),

            # Scraping parameters
            "start_urls": start_urls,
            "max_depth": self.job_config.get("crawlDepth", 3),
            "max_pages": self.job_config.get("maxPages", 100),

            # Rate limiting
            "rate_limit_min": rate_limit_min,
            "rate_limit_max": rate_limit_max,

            # Behavior
            "follow_links": self.job_config.get("followLinks", True),
            "respect_robots_txt": self.job_config.get("respectRobotsTxt", True),

            # Headers
            "headers": self.job_config.get("headers", {}),

            # Timeouts from base config
            "page_load_timeout": BaseConfig.PAGE_TIMEOUT,
            "product_page_timeout": BaseConfig.DETAIL_PAGE_TIMEOUT,

            # Output configuration
            "save_files": self.output_config.get("saveFiles", True),
            "file_format": self.output_config.get("fileFormat", "json"),

            # Selectors (if provided)
            "selectors": self.job_config.get("selectors", {}),

            # Authentication (if provided)
            "authentication": self.job_config.get("authentication"),
        }

        logger.info(f"Built scraper config for job {self.job_id}")
        return config

    def get_output_path(self) -> str:
        """
        Get output path for job results.

        Returns:
            Output directory path
        """
        from api.config import settings
        return f"{settings.STORAGE_JOBS_PATH}/{self.job_id}"

    def should_send_to_memento(self) -> bool:
        """
        Check if results should be sent to Memento.

        Returns:
            True if Memento integration is enabled
        """
        memento_config = self.output_config.get("sendToMemento")
        if memento_config:
            return memento_config.get("enabled", False)
        return False

    def get_memento_config(self) -> Dict[str, Any]:
        """
        Get Memento configuration.

        Returns:
            Memento configuration dictionary
        """
        return self.output_config.get("sendToMemento", {})

    def get_webhook_config(self) -> Dict[str, Any]:
        """
        Get webhook configuration.

        Returns:
            Webhook configuration dictionary or None
        """
        return self.output_config.get("webhook")
