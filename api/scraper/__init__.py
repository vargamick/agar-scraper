"""
Scraper integration layer.

Bridges the API job system with the existing scraper code.
"""

from api.scraper.adapter import ScraperAdapter
from api.scraper.config_builder import ConfigBuilder
from api.scraper.progress_reporter import ProgressReporter
from api.scraper.result_collector import ResultCollector

__all__ = [
    "ScraperAdapter",
    "ConfigBuilder",
    "ProgressReporter",
    "ResultCollector",
]
