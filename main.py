"""
3DN Multi-Client Scraper Template
Main orchestrator for client-specific scraping workflows
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Type

from config.config_loader import ConfigLoader
from config.base_config import BaseConfig
from core.category_scraper import CategoryScraper
from core.product_collector import ProductCollector
from core.product_scraper import ProductScraper
from core.product_pdf_scraper import ProductPDFScraper
from core.pdf_downloader import PDFDownloader
from core.utils import save_json, sanitize_filename


class ScraperOrchestrator:
    """Main orchestrator for complete scraping workflow"""
    
    def __init__(self, config: Type[BaseConfig], strategies, test_mode: bool = False):
        """Initialize orchestrator with configuration"""
        self.config = config
        self.strategies = strategies
        self.test_mode = test_mode
        
        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "_TEST" if test_mode else "_FULL"
        run_id = f"{config.CLIENT_NAME}Scrape_{timestamp}{mode_suffix}"
        self.run_dir = Path(config.BASE_OUTPUT_DIR) / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create base subdirectories (specialized modules will create their own substructure)
        (self.run_dir / "products").mkdir(exist_ok=True)
        (self.run_dir / "categories").mkdir(exist_ok=True)
        (self.run_dir / "screenshots").mkdir(exist_ok=True)
        (self.run_dir / "pdfs").mkdir(exist_ok=True)  # PDFDownloader creates PDS/SDS subdirs
        (self.run_dir / "reports").mkdir(exist_ok=True)
        (self.run_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize modules with config
        self.category_scraper = CategoryScraper(config, self.run_dir, test_mode)
        self.product_collector = ProductCollector(config, self.run_dir, test_mode)
        self.product_scraper = ProductScraper(config, strategies, self.run_dir, save_screenshots=True)
        self.pdf_scraper = ProductPDFScraper(config, self.run_dir)
        self.pdf_downloader = PDFDownloader(config, self.run_dir)
        
        self.run_id = run_id
        print(f"📁 Run directory: {self.run_dir}")
        print(f"📝 Run ID: {run_id}")
        
        if test_mode:
            print(f"⚠️  Test mode: Limited scraping enabled")
    
    async def run(self):
        """Execute complete scraping workflow"""
        start_time = datetime.now()
        
        try:
            # Step 1: Discover categories
            print("\n" + "="*60)
            print("STEP 1: DISCOVERING CATEGORIES")
            print("="*60)
            
            categories = await self.category_scraper.run()
            
            # Step 2: Collect product URLs
            print("\n" + "="*60)
            print("STEP 2: COLLECTING PRODUCT URLS")
            print("="*60)
            
            all_products = await self.product_collector.collect_all_products(categories)
            
            if not all_products:
                print("⚠️ No products found!")
                return
            
            # Apply test limit
            if self.test_mode and len(all_products) > self.config.TEST_PRODUCT_LIMIT:
                print(f"\n⚠️ Limiting to {self.config.TEST_PRODUCT_LIMIT} products for test mode")
                all_products = all_products[:self.config.TEST_PRODUCT_LIMIT]
            
            # Step 3: Scrape product details (CSS extraction)
            print("\n" + "="*60)
            print("STEP 3: SCRAPING PRODUCT DETAILS (CSS)")
            print("="*60)
            
            products_with_details = await self.product_scraper.scrape_products(all_products)
            
            if not products_with_details:
                print("⚠️ No product details extracted!")
                return
            
            # Step 4: Extract PDF links (JavaScript)
            print("\n" + "="*60)
            print("STEP 4: EXTRACTING PDF LINKS (JAVASCRIPT)")
            print("="*60)
            
            pdf_data_list = await self.pdf_scraper.scrape_products(products_with_details)
            
            # Step 5: Merge results
            print("\n" + "="*60)
            print("STEP 5: MERGING RESULTS")
            print("="*60)
            
            successful = self.merge_product_data(products_with_details, pdf_data_list)
            print(f"✓ Merged data for {len(successful)} products")
            
            # Step 6: Download PDF documents
            print("\n" + "="*60)
            print("STEP 6: DOWNLOADING PDF DOCUMENTS")
            print("="*60)
            
            download_stats = await self.pdf_downloader.download_all_pdfs(successful)
            
            # Generate final report
            self.generate_final_report(successful, all_products, start_time, download_stats)
            
            # Display summary
            self.display_summary(successful, all_products, start_time)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Scraping interrupted!")
            sys.exit(0)
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def merge_product_data(self, products_with_details: List[Dict], pdf_data_list: List[Dict]) -> List[Dict]:
        """Merge product details with PDF data"""
        
        # Create a lookup dict for PDF data by product name
        pdf_lookup = {}
        for pdf_data in pdf_data_list:
            product_name = pdf_data.get("product_name")
            if product_name:
                pdf_lookup[product_name] = pdf_data
        
        # Merge PDF data into product details
        merged = []
        for product in products_with_details:
            product_name = product.get("product_name")
            
            # Check if we have PDF data for this product
            if product_name in pdf_lookup:
                pdf_data = pdf_lookup[product_name]
                product["sds_url"] = pdf_data.get("sds_url")
                product["pds_url"] = pdf_data.get("pds_url")
                product["pdf_extraction_method"] = pdf_data.get("extraction_method")
                product["total_pdfs_found"] = pdf_data.get("total_pdfs_found", 0)
            else:
                # No PDF data found
                product["sds_url"] = None
                product["pds_url"] = None
                product["pdf_extraction_method"] = None
                product["total_pdfs_found"] = 0
            
            merged.append(product)
            
            # Re-save individual product file with merged data
            filename = sanitize_filename(product_name)
            save_json(product, self.run_dir / "products" / f"{filename}.json")
        
        return merged
    
    def generate_final_report(self, successful: List[Dict], all_products: List[Dict], start_time: datetime, download_stats: Dict = None):
        """Generate comprehensive final report"""
        
        # Download statistics
        products_with_sds = sum(1 for p in successful if p.get("sds_url"))
        products_with_pds = sum(1 for p in successful if p.get("pds_url"))
        products_with_both = sum(1 for p in successful if p.get("sds_url") and p.get("pds_url"))
        products_with_neither = len(successful) - products_with_sds - products_with_pds + products_with_both
        
        # Category breakdown
        category_stats = {}
        for product in successful:
            cat = product.get("category", "Unknown")
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "with_sds": 0, "with_pds": 0}
            category_stats[cat]["count"] += 1
            if product.get("sds_url"):
                category_stats[cat]["with_sds"] += 1
            if product.get("pds_url"):
                category_stats[cat]["with_pds"] += 1
        
        report = {
            "run_id": self.run_id,
            "client": self.config.CLIENT_NAME,
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": str(datetime.now() - start_time),
            "mode": "TEST" if self.test_mode else "FULL",
            "statistics": {
                "total_attempted": len(all_products),
                "total_scraped": len(successful),
                "total_failed": len(all_products) - len(successful),
                "success_rate": f"{(len(successful) / len(all_products) * 100):.1f}%" if all_products else "0%"
            },
            "download_statistics": {
                "products_with_sds": products_with_sds,
                "products_with_pds": products_with_pds,
                "products_with_both": products_with_both,
                "products_with_neither": products_with_neither
            },
            "pdf_download_statistics": download_stats if download_stats else {},
            "category_breakdown": category_stats
        }
        
        # Save report
        save_json(report, self.run_dir / "reports" / "final_report.json")
        
        # Save all scraped products
        save_json(successful, self.run_dir / "all_products_data.json")
    
    def display_summary(self, successful: List[Dict], all_products: List[Dict], start_time: datetime):
        """Display final summary"""
        print("\n" + "="*60)
        print("✅ SCRAPING COMPLETED!")
        print("="*60)
        print(f"📊 Successfully scraped: {len(successful)}/{len(all_products)} products")
        
        # Download statistics
        products_with_sds = sum(1 for p in successful if p.get("sds_url"))
        products_with_pds = sum(1 for p in successful if p.get("pds_url"))
        
        print(f"\n📄 Download Statistics:")
        print(f"   - Products with SDS: {products_with_sds}")
        print(f"   - Products with PDS: {products_with_pds}")
        
        print(f"\n⏱️  Total time: {datetime.now() - start_time}")
        print(f"📁 Results saved to: {self.run_dir.absolute()}")
        print("="*60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="3DN Multi-Client Scraper Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --client agar --test    # Test Agar scraper (2 categories)
  python main.py --client agar --full    # Full Agar scrape
  python main.py --client xyz --test     # Test another client

Available Clients:
  - agar    : Agar Cleaning Products (agar.com.au)
  
Add new clients by creating:
  config/clients/[client_name]/client_config.py
  config/clients/[client_name]/extraction_strategies.py
        """
    )
    
    parser.add_argument('--client', '-c', type=str, required=True,
                       help='Client name (e.g., agar)')
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', '-t', action='store_true',
                           help='Test mode (limited scraping)')
    mode_group.add_argument('--full', '-f', action='store_true',
                           help='Full scrape mode')
    
    args = parser.parse_args()
    
    # Load client configuration and strategies
    try:
        config = ConfigLoader.load_client_config(args.client)
        strategies = ConfigLoader.load_client_strategies(args.client)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nAvailable clients:")
        print(f"  - agar")
        print(f"\nTo add a new client, create:")
        print(f"  config/clients/{args.client}/client_config.py")
        print(f"  config/clients/{args.client}/extraction_strategies.py")
        sys.exit(1)
    
    # Display header
    print("\n" + "="*60)
    print(f"{'3DN SCRAPER - ' + config.CLIENT_NAME.upper():^60}")
    print("="*60)
    
    # Create and run orchestrator
    orchestrator = ScraperOrchestrator(
        config=config,
        strategies=strategies,
        test_mode=args.test
    )
    
    await orchestrator.run()


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print(f"❌ Error: Python 3.11+ required (you have {sys.version})")
        sys.exit(1)
    
    asyncio.run(main())
