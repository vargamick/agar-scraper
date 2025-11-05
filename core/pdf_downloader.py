"""
PDF Downloader Module for Agar Scraper
Downloads actual PDF files from scraped URLs
"""
import asyncio
import aiohttp
import json
import ssl
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys

from typing import Type
from config.base_config import BaseConfig
from core.utils import sanitize_filename, save_json


class PDFDownloader:
    """Downloads PDF files from URLs with retry logic and error handling"""
    
    def __init__(self, config: Type[BaseConfig], run_dir: Path, max_retries: int = 3, timeout: int = 30):
        """
        Initialize PDF downloader
        
        Args:
            config: Client configuration object
            run_dir: Run directory path
            max_retries: Maximum number of download retry attempts
            timeout: Timeout in seconds for each download
        """
        self.config = config
        self.run_dir = Path(run_dir)
        self.pdf_output_dir = self.run_dir / "PDFs"
        self.pdf_metadata_dir = self.run_dir / "pdfs"
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Statistics
        self.stats = {
            "total_pdfs": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "skipped": 0,
            "total_size_bytes": 0
        }
        
        # Ensure output directory exists
        self.pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_all_pdfs(self, products: Optional[List[Dict]] = None) -> Dict:
        """
        Download all PDFs for scraped products
        
        Args:
            products: Optional list of product data. If None, reads from pdf metadata files
            
        Returns:
            Dictionary containing download statistics
        """
        print("\n" + "="*60)
        print("DOWNLOADING PDF DOCUMENTS")
        print("="*60)
        
        # Get PDF metadata either from products or from files
        pdf_metadata_list = []
        
        if products:
            # Extract PDF URLs from product data
            for product in products:
                if product.get("sds_url") or product.get("pds_url"):
                    pdf_metadata_list.append({
                        "product_name": product.get("product_name"),
                        "sds_url": product.get("sds_url"),
                        "pds_url": product.get("pds_url")
                    })
        else:
            # Read from PDF metadata files
            if not self.pdf_metadata_dir.exists():
                print(f"❌ PDF metadata directory not found: {self.pdf_metadata_dir}")
                return self.stats
            
            pdf_metadata_list = self._load_pdf_metadata()
        
        if not pdf_metadata_list:
            print("⚠️  No PDFs to download")
            return self.stats
        
        print(f"📄 Found {len(pdf_metadata_list)} products with PDF metadata")
        
        # Download PDFs
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            for idx, pdf_metadata in enumerate(pdf_metadata_list, 1):
                print(f"\n[PDF Download {idx}/{len(pdf_metadata_list)}] {pdf_metadata['product_name']}")
                
                await self._download_product_pdfs(session, pdf_metadata)
        
        # Display statistics
        self._display_statistics()
        
        # Save download report
        self._save_download_report()
        
        return self.stats
    
    def _load_pdf_metadata(self) -> List[Dict]:
        """Load PDF metadata from JSON files"""
        pdf_metadata_list = []
        
        for pdf_file in self.pdf_metadata_dir.glob("*_pdfs.json"):
            try:
                with open(pdf_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    pdf_metadata_list.append(metadata)
            except Exception as e:
                print(f"⚠️  Error reading {pdf_file.name}: {e}")
        
        return pdf_metadata_list
    
    async def _download_product_pdfs(self, session: aiohttp.ClientSession, pdf_metadata: Dict):
        """Download SDS and PDS PDFs for a single product"""
        product_name = pdf_metadata.get("product_name")
        sds_url = pdf_metadata.get("sds_url")
        pds_url = pdf_metadata.get("pds_url")
        
        if not product_name:
            print("  ⚠️  Skipping: No product name")
            return
        
        # Create product subdirectory
        safe_product_name = sanitize_filename(product_name)
        product_pdf_dir = self.pdf_output_dir / safe_product_name
        product_pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Download SDS
        if sds_url:
            await self._download_single_pdf(
                session, 
                sds_url, 
                product_pdf_dir / f"{safe_product_name}_SDS.pdf",
                "SDS"
            )
        else:
            print("  ⚠️  No SDS URL available")
        
        # Download PDS
        if pds_url:
            await self._download_single_pdf(
                session, 
                pds_url, 
                product_pdf_dir / f"{safe_product_name}_PDS.pdf",
                "PDS"
            )
        else:
            print("  ⚠️  No PDS URL available")
    
    async def _download_single_pdf(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        output_path: Path,
        pdf_type: str
    ) -> bool:
        """
        Download a single PDF file with retry logic
        
        Args:
            session: aiohttp session
            url: PDF URL to download
            output_path: Where to save the PDF
            pdf_type: Type of PDF (SDS or PDS) for logging
            
        Returns:
            True if successful, False otherwise
        """
        self.stats["total_pdfs"] += 1
        
        # Check if file already exists
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"  ✓ {pdf_type} already exists ({self._format_size(file_size)})")
            self.stats["skipped"] += 1
            self.stats["total_size_bytes"] += file_size
            return True
        
        # Attempt download with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"  → Downloading {pdf_type}... ", end="", flush=True)
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Verify it's actually a PDF
                        if not content.startswith(b'%PDF'):
                            print(f"❌ Not a valid PDF file")
                            self.stats["failed_downloads"] += 1
                            return False
                        
                        # Save PDF
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        file_size = len(content)
                        self.stats["successful_downloads"] += 1
                        self.stats["total_size_bytes"] += file_size
                        
                        print(f"✓ ({self._format_size(file_size)})")
                        return True
                    else:
                        print(f"❌ HTTP {response.status}")
                        if attempt < self.max_retries:
                            print(f"  ↻ Retry {attempt}/{self.max_retries}...")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            except asyncio.TimeoutError:
                print(f"❌ Timeout")
                if attempt < self.max_retries:
                    print(f"  ↻ Retry {attempt}/{self.max_retries}...")
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                if attempt < self.max_retries:
                    print(f"  ↻ Retry {attempt}/{self.max_retries}...")
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        self.stats["failed_downloads"] += 1
        return False
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _display_statistics(self):
        """Display download statistics"""
        print("\n" + "="*60)
        print("📊 DOWNLOAD STATISTICS")
        print("="*60)
        print(f"Total PDFs attempted:    {self.stats['total_pdfs']}")
        print(f"Successful downloads:    {self.stats['successful_downloads']}")
        print(f"Failed downloads:        {self.stats['failed_downloads']}")
        print(f"Skipped (already exist): {self.stats['skipped']}")
        print(f"Total size:              {self._format_size(self.stats['total_size_bytes'])}")
        
        if self.stats['total_pdfs'] > 0:
            success_rate = (self.stats['successful_downloads'] + self.stats['skipped']) / self.stats['total_pdfs'] * 100
            print(f"Success rate:            {success_rate:.1f}%")
        
        print("="*60)
    
    def _save_download_report(self):
        """Save download report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "output_directory": str(self.pdf_output_dir),
            "success_rate": f"{(self.stats['successful_downloads'] + self.stats['skipped']) / self.stats['total_pdfs'] * 100:.1f}%" if self.stats['total_pdfs'] > 0 else "0%"
        }
        
        reports_dir = self.run_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        save_json(report, reports_dir / "pdf_download_report.json")
        print(f"📄 Download report saved to: {reports_dir / 'pdf_download_report.json'}")


async def main():
    """Standalone script to download PDFs from a scraping run"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download PDF documents from Agar scraper run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_downloader.py -r agar_scrapes/AgarScrape_20251031_145940_TEST
  python pdf_downloader.py --run-dir path/to/run --retries 5

This will:
  1. Read PDF metadata from the run's pdfs/ directory
  2. Download SDS and PDS files to the run's PDFs/ directory
  3. Organize PDFs by product name
  4. Skip files that already exist
  5. Retry failed downloads up to --retries times
        """
    )
    
    parser.add_argument(
        '-r', '--run-dir',
        type=str,
        required=True,
        help='Path to scraping run directory'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts (default: 3)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Download timeout in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    run_dir = Path(args.run_dir)
    
    if not run_dir.exists():
        print(f"❌ Run directory not found: {run_dir}")
        sys.exit(1)
    
    if not (run_dir / "pdfs").exists():
        print(f"❌ PDF metadata directory not found: {run_dir / 'pdfs'}")
        print("   Make sure you've run the scraper to extract PDF URLs first")
        sys.exit(1)
    
    print("\n" + "="*60)
    print(" AGAR PDF DOWNLOADER".center(60))
    print("="*60)
    print(f"📁 Run directory: {run_dir.absolute()}")
    print(f"🔄 Max retries: {args.retries}")
    print(f"⏱️  Timeout: {args.timeout}s")
    
    downloader = PDFDownloader(run_dir, max_retries=args.retries, timeout=args.timeout)
    await downloader.download_all_pdfs()
    
    print(f"\n✅ PDFs saved to: {downloader.pdf_output_dir.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
