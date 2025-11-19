"""
Scraper Data Discovery Module

This module provides a simple interface for downstream applications to discover
and access the latest scraped data for processing (vector embeddings, knowledge
graph population, etc.).

Usage:
    from scraper_data_discovery import ScraperDataDiscovery

    discovery = ScraperDataDiscovery(db_config)
    latest_run = discovery.get_latest_completed_run(client_name="agar")

    # Access the data
    print(f"Data location: {latest_run['output_path']}")
    print(f"Products file: {latest_run['all_products_json']}")
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional
import os


class ScraperDataDiscovery:
    """
    Helper class to discover latest scraper runs for downstream processing.

    This class provides methods to query the scraper database and find the
    latest completed scrape runs, making it easy for downstream applications
    to locate and process scraped data.
    """

    def __init__(self, db_config: Dict[str, str], base_path: str = "/app/scraper_data/jobs"):
        """
        Initialize with database connection config.

        Args:
            db_config: Dict with keys: host, port, database, user, password
            base_path: Base path where scraper data is stored (default: /app/scraper_data/jobs)

        Example:
            db_config = {
                "host": "localhost",
                "port": 5432,
                "database": "scraper_db",
                "user": "scraper_user",
                "password": "scraper_password"
            }
        """
        self.db_config = db_config
        self.base_path = base_path

    def _get_connection(self):
        """Create and return a database connection."""
        return psycopg2.connect(**self.db_config)

    def get_latest_completed_run(self, client_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get the most recent completed scrape run.

        Args:
            client_name: Optional filter by client (e.g., 'agar')

        Returns:
            Dict with job metadata and output paths, or None if no runs found

        Example:
            >>> discovery = ScraperDataDiscovery(db_config)
            >>> latest = discovery.get_latest_completed_run(client_name="agar")
            >>> print(latest['output_path'])
            /app/scraper_data/jobs/20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8
        """
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                id,
                name,
                folder_name,
                status,
                created_at,
                started_at,
                completed_at,
                stats,
                config,
                progress
            FROM jobs
            WHERE status = 'completed'
              AND type = 'web'
        """

        params = []
        if client_name:
            query += " AND config->>'client_name' = %s"
            params.append(client_name)

        query += " ORDER BY completed_at DESC LIMIT 1"

        cur.execute(query, params)
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return None

        # Construct full output path
        job_id = str(row['id'])
        folder_name = row['folder_name']
        full_folder_name = f"{folder_name}_{job_id}"
        output_path = f"{self.base_path}/{full_folder_name}"

        result = {
            # Identity
            "job_id": job_id,
            "name": row['name'],

            # Folder information
            "folder_name": folder_name,
            "full_folder_name": full_folder_name,
            "output_path": output_path,

            # Status
            "status": row['status'],

            # Timestamps
            "created_at": row['created_at'],
            "started_at": row['started_at'],
            "completed_at": row['completed_at'],

            # Metadata
            "stats": row['stats'],
            "config": row['config'],
            "progress": row['progress'],

            # Convenience paths to data files
            "all_products_json": f"{output_path}/all_products.json",
            "categories_json": f"{output_path}/categories.json",
            "results_json": f"{output_path}/results.json",
            "pdfs_dir": f"{output_path}/pdfs",
            "screenshots_dir": f"{output_path}/screenshots",

            # Computed fields
            "items_extracted": row['stats'].get('itemsExtracted', 0) if row['stats'] else 0,
            "duration_seconds": (
                (row['completed_at'] - row['started_at']).total_seconds()
                if row['completed_at'] and row['started_at'] else None
            ),
        }

        cur.close()
        conn.close()

        return result

    def get_runs_since(self, last_processed_timestamp: datetime, client_name: Optional[str] = None) -> List[Dict]:
        """
        Get all completed runs since a given timestamp.

        This is useful for batch processing or catching up on missed runs.

        Args:
            last_processed_timestamp: datetime object or ISO string
            client_name: Optional filter by client

        Returns:
            List of dicts with job metadata, ordered by completion time (oldest first)

        Example:
            >>> from datetime import datetime
            >>> last_run = datetime(2025, 11, 14, 0, 0, 0)
            >>> new_runs = discovery.get_runs_since(last_run)
            >>> for run in new_runs:
            ...     print(f"Process: {run['output_path']}")
        """
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                id,
                name,
                folder_name,
                completed_at,
                stats,
                config
            FROM jobs
            WHERE status = 'completed'
              AND type = 'web'
              AND completed_at > %s
        """

        params = [last_processed_timestamp]
        if client_name:
            query += " AND config->>'client_name' = %s"
            params.append(client_name)

        query += " ORDER BY completed_at ASC"

        cur.execute(query, params)
        rows = cur.fetchall()

        results = []
        for row in rows:
            job_id = str(row['id'])
            folder_name = row['folder_name']
            full_folder_name = f"{folder_name}_{job_id}"
            output_path = f"{self.base_path}/{full_folder_name}"

            results.append({
                "job_id": job_id,
                "name": row['name'],
                "folder_name": folder_name,
                "full_folder_name": full_folder_name,
                "output_path": output_path,
                "completed_at": row['completed_at'],
                "items_extracted": row['stats'].get('itemsExtracted', 0) if row['stats'] else 0,
                "all_products_json": f"{output_path}/all_products.json",
                "categories_json": f"{output_path}/categories.json",
            })

        cur.close()
        conn.close()

        return results

    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """
        Get a specific job by its UUID.

        Args:
            job_id: Job UUID as string

        Returns:
            Dict with job metadata, or None if not found

        Example:
            >>> job = discovery.get_job_by_id("73395058-e599-4bf7-a35f-79da2264afa8")
            >>> print(job['status'])
            completed
        """
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                id,
                name,
                folder_name,
                status,
                created_at,
                started_at,
                completed_at,
                stats,
                config,
                progress
            FROM jobs
            WHERE id = %s
        """

        cur.execute(query, (job_id,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return None

        # Construct paths
        job_id = str(row['id'])
        folder_name = row['folder_name']
        full_folder_name = f"{folder_name}_{job_id}"
        output_path = f"{self.base_path}/{full_folder_name}"

        result = {
            "job_id": job_id,
            "name": row['name'],
            "folder_name": folder_name,
            "full_folder_name": full_folder_name,
            "output_path": output_path,
            "status": row['status'],
            "created_at": row['created_at'],
            "started_at": row['started_at'],
            "completed_at": row['completed_at'],
            "stats": row['stats'],
            "config": row['config'],
            "progress": row['progress'],
            "all_products_json": f"{output_path}/all_products.json",
            "categories_json": f"{output_path}/categories.json",
        }

        cur.close()
        conn.close()

        return result

    def check_data_exists(self, job_info: Dict) -> Dict[str, bool]:
        """
        Check which data files exist for a given job.

        Args:
            job_info: Job info dict from get_latest_completed_run() or similar

        Returns:
            Dict with boolean flags for each file type

        Example:
            >>> latest = discovery.get_latest_completed_run()
            >>> exists = discovery.check_data_exists(latest)
            >>> if exists['all_products_json']:
            ...     print("Products file ready for processing")
        """
        output_path = job_info['output_path']

        return {
            "all_products_json": os.path.exists(f"{output_path}/all_products.json"),
            "categories_json": os.path.exists(f"{output_path}/categories.json"),
            "results_json": os.path.exists(f"{output_path}/results.json"),
            "pdfs_dir": os.path.isdir(f"{output_path}/pdfs"),
            "screenshots_dir": os.path.isdir(f"{output_path}/screenshots"),
        }


def main():
    """Example usage of ScraperDataDiscovery."""

    # Database configuration
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "scraper_db"),
        "user": os.getenv("DB_USER", "scraper_user"),
        "password": os.getenv("DB_PASSWORD", "scraper_password")
    }

    # Initialize discovery helper
    discovery = ScraperDataDiscovery(db_config)

    # Get latest run for Agar client
    print("Fetching latest completed run for Agar...")
    latest_run = discovery.get_latest_completed_run(client_name="agar")

    if latest_run:
        print(f"\n✓ Found latest run:")
        print(f"  Name: {latest_run['name']}")
        print(f"  Job ID: {latest_run['job_id']}")
        print(f"  Completed: {latest_run['completed_at']}")
        print(f"  Items: {latest_run['items_extracted']}")
        print(f"  Duration: {latest_run['duration_seconds']:.1f}s")
        print(f"\n  Output Path: {latest_run['output_path']}")
        print(f"  Products JSON: {latest_run['all_products_json']}")

        # Check if files exist
        exists = discovery.check_data_exists(latest_run)
        print(f"\n  Data files:")
        for file_type, exists_flag in exists.items():
            status = "✓" if exists_flag else "✗"
            print(f"    {status} {file_type}")

        # Now you can load and process the data
        if exists['all_products_json']:
            import json
            with open(latest_run['all_products_json'], 'r') as f:
                products = json.load(f)
                print(f"\n  Loaded {len(products)} products for processing")
                print(f"  First product: {products[0]['product_name']}")
    else:
        print("✗ No completed runs found")

    # Example: Get all runs since a specific date
    print("\n" + "="*60)
    print("Checking for new runs since 2025-11-14...")
    from datetime import datetime
    last_processed = datetime(2025, 11, 14, 0, 0, 0)
    new_runs = discovery.get_runs_since(last_processed)

    print(f"Found {len(new_runs)} new runs")
    for run in new_runs:
        print(f"  - {run['name']} ({run['completed_at']}): {run['items_extracted']} items")


if __name__ == "__main__":
    main()
