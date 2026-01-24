"""
Matrix Processor

Main orchestrator for processing Product Application Matrix
and sending data to the Memento knowledge graph.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from api.config import settings
from api.integrations.memento.client import MementoClient
from api.integrations.memento.schemas import ProcessingResult
from .parser import MatrixParser, MatrixRow
from .entity_extractor import EntityExtractor
from .product_matcher import ProductMatcher, MatchReport
from .relationship_builder import RelationshipBuilder

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Configuration for matrix processor."""
    matrix_file_path: Path
    scraped_products_path: Optional[Path] = None
    memento_instance_id: Optional[str] = None
    memento_api_url: Optional[str] = None
    memento_api_key: Optional[str] = None
    match_threshold: float = 0.85
    dry_run: bool = False


class MatrixProcessor:
    """
    Process Product Application Matrix and send to Memento.

    Orchestrates the full pipeline:
    1. Parse matrix file
    2. Load scraped products (optional)
    3. Match matrix products to scraped products
    4. Extract and normalize entities
    5. Build relationships
    6. Send to Memento API
    """

    def __init__(self, config: ProcessorConfig):
        """
        Initialize processor.

        Args:
            config: Processor configuration
        """
        self.config = config

        # Initialize components
        self.parser = MatrixParser(config.matrix_file_path)
        self.extractor = EntityExtractor()
        self.matcher: Optional[ProductMatcher] = None

        # Memento client (initialized lazily)
        self._client: Optional[MementoClient] = None

        logger.info(f"MatrixProcessor initialized for {config.matrix_file_path}")

    @property
    def client(self) -> MementoClient:
        """Get or create Memento client."""
        if self._client is None:
            self._client = MementoClient(
                instance_id=self.config.memento_instance_id,
                api_url=self.config.memento_api_url,
                api_key=self.config.memento_api_key,
            )
        return self._client

    async def process(self) -> ProcessingResult:
        """
        Run the complete matrix processing pipeline.

        Returns:
            ProcessingResult with statistics and status
        """
        start_time = time.time()
        errors: List[str] = []

        try:
            # Step 1: Parse matrix
            logger.info("Step 1: Parsing matrix file...")
            rows = self.parser.parse()
            logger.info(f"Parsed {len(rows)} products from matrix")

            # Step 2: Load scraped products (if path provided)
            scraped_products = []
            if self.config.scraped_products_path:
                logger.info("Step 2: Loading scraped products...")
                scraped_products = self._load_scraped_products()
                logger.info(f"Loaded {len(scraped_products)} scraped products")

            # Step 3: Match products
            match_report = None
            if scraped_products:
                logger.info("Step 3: Matching products...")
                self.matcher = ProductMatcher(
                    scraped_products,
                    match_threshold=self.config.match_threshold,
                )
                match_report = self.matcher.get_match_report(rows)
                logger.info(
                    f"Matched {len(match_report.matched)}/{len(rows)} products "
                    f"({match_report.match_rate:.1%})"
                )

            # Step 4: Extract entities
            logger.info("Step 4: Extracting entities...")
            extraction_result = self.extractor.extract_entities(rows)
            entity_stats = self.extractor.get_entity_stats(extraction_result)
            logger.info(f"Entity counts: {entity_stats}")

            # Step 5 & 6: Build relationships and send to Memento
            entities_created = 0
            relationships_created = 0

            if not self.config.dry_run:
                logger.info("Step 5: Building relationships and sending to Memento...")
                async with self.client:
                    builder = RelationshipBuilder(self.client, self.extractor)
                    build_result = await builder.build_from_rows(rows)

                    entities_created = build_result.entities_created
                    relationships_created = build_result.relationships_created
                    errors.extend(build_result.errors)
            else:
                logger.info("Step 5: DRY RUN - skipping Memento upload")
                # In dry run, count what would be created
                entities_created = extraction_result.entity_count
                relationships_created = self._count_relationships(rows)

            processing_time = time.time() - start_time

            result = ProcessingResult(
                success=len(errors) == 0,
                entities_created=entities_created,
                relationships_created=relationships_created,
                products_matched=len(match_report.matched) if match_report else 0,
                products_unmatched=len(match_report.unmatched) if match_report else 0,
                errors=errors,
                processing_time_seconds=processing_time,
            )

            logger.info(
                f"Processing complete in {processing_time:.2f}s: "
                f"{entities_created} entities, {relationships_created} relationships"
            )

            return result

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=time.time() - start_time,
            )

    def _load_scraped_products(self) -> List[Dict[str, Any]]:
        """Load scraped products from JSON file."""
        if not self.config.scraped_products_path:
            return []

        path = Path(self.config.scraped_products_path)
        if not path.exists():
            logger.warning(f"Scraped products file not found: {path}")
            return []

        try:
            with open(path, "r") as f:
                products = json.load(f)

            if isinstance(products, list):
                return products
            elif isinstance(products, dict) and "products" in products:
                return products["products"]
            else:
                logger.warning(f"Unexpected format in {path}")
                return []

        except Exception as e:
            logger.error(f"Failed to load scraped products: {e}")
            return []

    def _count_relationships(self, rows: List[MatrixRow]) -> int:
        """Count total relationships that would be created."""
        count = 0
        for row in rows:
            count += len(row.surfaces)  # SUITABLE_FOR
            count += len(row.incompatible_surfaces)  # INCOMPATIBLE_WITH
            count += len(row.soilage_types)  # HANDLES
            count += len(row.incompatible_soilage)  # UNSUITABLE_FOR
            count += len(row.locations)  # USED_IN
            count += len(row.benefits)  # HAS_BENEFIT
        return count

    def get_preview(self) -> Dict[str, Any]:
        """
        Get a preview of what would be processed.

        Useful for dry runs and validation.
        """
        rows = self.parser.parse()
        summary = self.parser.get_summary(rows)
        extraction_result = self.extractor.extract_entities(rows)

        return {
            "matrix_file": str(self.config.matrix_file_path),
            "products": summary["total_products"],
            "entity_counts": self.extractor.get_entity_stats(extraction_result),
            "unique_surfaces": summary["unique_surfaces"],
            "unique_locations": summary["unique_locations"],
            "estimated_relationships": self._count_relationships(rows),
            "sample_products": [
                {
                    "name": rows[i].product_name,
                    "surfaces": rows[i].surfaces[:3],
                    "locations": rows[i].locations[:3],
                }
                for i in range(min(5, len(rows)))
            ],
        }


async def process_matrix(
    matrix_file_path: str,
    scraped_products_path: Optional[str] = None,
    memento_instance_id: Optional[str] = None,
    dry_run: bool = False,
) -> ProcessingResult:
    """
    Convenience function to process a matrix file.

    Args:
        matrix_file_path: Path to the matrix CSV/Excel file
        scraped_products_path: Path to scraped all_products.json
        memento_instance_id: Memento instance ID (uses default if not specified)
        dry_run: If True, don't actually send to Memento

    Returns:
        ProcessingResult
    """
    config = ProcessorConfig(
        matrix_file_path=Path(matrix_file_path),
        scraped_products_path=Path(scraped_products_path) if scraped_products_path else None,
        memento_instance_id=memento_instance_id or settings.MEMENTO_DEFAULT_INSTANCE,
        dry_run=dry_run,
    )

    processor = MatrixProcessor(config)
    return await processor.process()
