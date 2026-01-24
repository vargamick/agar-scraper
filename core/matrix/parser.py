"""
Matrix Parser

Parses Product Application Matrix from CSV/Excel files.
Handles the multi-row format where each product spans multiple rows
with related entity values.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)


class MatrixParseError(Exception):
    """Raised when matrix parsing fails."""
    pass


@dataclass
class MatrixRow:
    """
    Represents a parsed product with all its related entities.

    Each MatrixRow aggregates all values from the multi-row
    format in the source Excel file.
    """
    product_name: str
    benefits: List[str] = field(default_factory=list)
    surfaces: List[str] = field(default_factory=list)
    incompatible_surfaces: List[str] = field(default_factory=list)
    soilage_types: List[str] = field(default_factory=list)
    incompatible_soilage: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "product_name": self.product_name,
            "benefits": self.benefits,
            "surfaces": self.surfaces,
            "incompatible_surfaces": self.incompatible_surfaces,
            "soilage_types": self.soilage_types,
            "incompatible_soilage": self.incompatible_soilage,
            "locations": self.locations,
        }


class MatrixParser:
    """
    Parse Product Application Matrix from CSV/Excel files.

    Handles the multi-row format where a product name appears on one row,
    and subsequent rows (with empty product name) contain additional
    values for the same product.

    Example input format:
    | Product    | Key Benefits | Surface      | ...
    | 3D-GLOSS   | Shiny        | Vinyl        | ...
    |            | Non-slip     | Timber       | ...
    |            | Durable      | Stone        | ...
    | ACID WASH  | Cleans       | Ceramic      | ...
    """

    # Expected column names (case-insensitive matching)
    COLUMN_MAPPING = {
        "product": "product_name",
        "key benefits": "benefits",
        "surface": "surfaces",
        "incompatible surface": "incompatible_surfaces",
        "soilage": "soilage_types",
        "incompatible soilage": "incompatible_soilage",
        "location / area": "locations",
        "location/area": "locations",
    }

    # Values to treat as empty/null
    NULL_VALUES = {"not stated", "n/a", "na", "none", "-", ""}

    def __init__(self, file_path: Path):
        """
        Initialize parser with file path.

        Args:
            file_path: Path to CSV or Excel file
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise MatrixParseError(f"File not found: {self.file_path}")

    def parse(self) -> List[MatrixRow]:
        """
        Parse the matrix file and return list of MatrixRow objects.

        Returns:
            List of MatrixRow objects, one per product
        """
        logger.info(f"Parsing matrix file: {self.file_path}")

        # Load dataframe
        df = self._load_file()

        # Find and validate columns
        df = self._normalize_columns(df)

        # Parse into MatrixRow objects
        rows = self._parse_rows(df)

        logger.info(f"Parsed {len(rows)} products from matrix")
        return rows

    def _load_file(self) -> pd.DataFrame:
        """Load file into DataFrame."""
        suffix = self.file_path.suffix.lower()

        try:
            if suffix == ".csv":
                # Try to detect header row
                df = pd.read_csv(self.file_path)
            elif suffix in [".xlsx", ".xls"]:
                # Excel files - try to find the header row
                df = pd.read_excel(self.file_path, header=None)

                # Find the row with "Product" in first column
                header_row = self._find_header_row(df)
                if header_row is not None:
                    df = pd.read_excel(self.file_path, header=header_row)
                else:
                    raise MatrixParseError("Could not find header row with 'Product' column")
            else:
                raise MatrixParseError(f"Unsupported file type: {suffix}")

        except Exception as e:
            if isinstance(e, MatrixParseError):
                raise
            raise MatrixParseError(f"Failed to load file: {e}")

        return df

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find the row index containing column headers."""
        for idx, row in df.iterrows():
            # Check if this row looks like headers
            row_values = [str(v).lower().strip() for v in row.values if pd.notna(v)]
            if "product" in row_values:
                return idx
        return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format."""
        # Create mapping from actual columns to normalized names
        column_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower in self.COLUMN_MAPPING:
                column_map[col] = self.COLUMN_MAPPING[col_lower]

        # Check required columns
        normalized_cols = set(column_map.values())
        if "product_name" not in normalized_cols:
            raise MatrixParseError(
                f"Missing required 'Product' column. Found: {list(df.columns)}"
            )

        # Rename columns
        df = df.rename(columns=column_map)

        # Keep only mapped columns
        valid_cols = [c for c in df.columns if c in self.COLUMN_MAPPING.values()]
        df = df[valid_cols]

        logger.debug(f"Normalized columns: {valid_cols}")
        return df

    def _parse_rows(self, df: pd.DataFrame) -> List[MatrixRow]:
        """Parse DataFrame rows into MatrixRow objects."""
        products = []
        current_product: Optional[MatrixRow] = None

        for _, row in df.iterrows():
            product_name = self._clean_value(row.get("product_name"))

            # Skip rows that are repeated headers
            if product_name and product_name.lower() == "product":
                continue

            if product_name:
                # New product - save previous if exists
                if current_product:
                    products.append(current_product)

                # Start new product
                current_product = MatrixRow(product_name=product_name)
                self._add_row_values(current_product, row)

            elif current_product:
                # Continuation row - add values to current product
                self._add_row_values(current_product, row)

        # Don't forget the last product
        if current_product:
            products.append(current_product)

        return products

    def _add_row_values(self, product: MatrixRow, row: pd.Series):
        """Add values from a row to the product."""
        # Benefits
        value = self._clean_value(row.get("benefits"))
        if value and value not in product.benefits:
            product.benefits.append(value)

        # Surfaces
        value = self._clean_value(row.get("surfaces"))
        if value and value not in product.surfaces:
            product.surfaces.append(value)

        # Incompatible surfaces
        value = self._clean_value(row.get("incompatible_surfaces"))
        if value and value not in product.incompatible_surfaces:
            product.incompatible_surfaces.append(value)

        # Soilage
        value = self._clean_value(row.get("soilage_types"))
        if value and value not in product.soilage_types:
            product.soilage_types.append(value)

        # Incompatible soilage
        value = self._clean_value(row.get("incompatible_soilage"))
        if value and value not in product.incompatible_soilage:
            product.incompatible_soilage.append(value)

        # Locations
        value = self._clean_value(row.get("locations"))
        if value and value not in product.locations:
            product.locations.append(value)

    def _clean_value(self, value: Any) -> Optional[str]:
        """Clean and validate a cell value."""
        if pd.isna(value):
            return None

        value = str(value).strip()

        # Check for null values
        if value.lower() in self.NULL_VALUES:
            return None

        return value

    def get_summary(self, rows: List[MatrixRow]) -> Dict[str, Any]:
        """
        Generate summary statistics for parsed data.

        Args:
            rows: List of parsed MatrixRow objects

        Returns:
            Dictionary with summary statistics
        """
        all_surfaces = set()
        all_incompatible_surfaces = set()
        all_soilage = set()
        all_locations = set()
        all_benefits = set()

        for row in rows:
            all_surfaces.update(row.surfaces)
            all_incompatible_surfaces.update(row.incompatible_surfaces)
            all_soilage.update(row.soilage_types)
            all_locations.update(row.locations)
            all_benefits.update(row.benefits)

        return {
            "total_products": len(rows),
            "unique_surfaces": len(all_surfaces),
            "unique_incompatible_surfaces": len(all_incompatible_surfaces),
            "unique_soilage_types": len(all_soilage),
            "unique_locations": len(all_locations),
            "unique_benefits": len(all_benefits),
            "surfaces": sorted(all_surfaces),
            "locations": sorted(all_locations),
        }
