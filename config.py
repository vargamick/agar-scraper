"""
Configuration and constants for Agar scraper
"""
from pathlib import Path
from datetime import datetime

# Base configuration
BASE_URL = "https://agar.com.au"
BASE_OUTPUT_DIR = "agar_scrapes"

# Test mode limits
TEST_CATEGORY_LIMIT = 2
TEST_PRODUCT_LIMIT = 5

# Timeouts and delays
PAGE_TIMEOUT = 60000  # 60 seconds
DETAIL_PAGE_TIMEOUT = 35000  # 35 seconds for product details
RATE_LIMIT_DELAY = 2  # seconds between requests

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Known categories (fallback if discovery fails)
KNOWN_CATEGORIES = [
    "toilet-bathroom-cleaners",
    "green-cleaning-products", 
    "vehicle-cleaning",
    "hard-floor-care",
    "specialty-cleaning",
    "disinfectants-antibacterials",
    "kitchen-cleaners",
    "carpet-upholstery",
    "laundry-products",
    "air-fresheners",
    "hand-soaps-sanitisers",
    "all-purpose-floor-cleaners",
    "chlorinated-cleaners-sanitisers",
    "floor-care"
]

def create_run_directory(base_dir: str = BASE_OUTPUT_DIR, test_mode: bool = False) -> Path:
    """Create a timestamped run directory"""
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"AgarScrape_{timestamp}"
    if test_mode:
        run_name += "_TEST"
    
    run_dir = base_path / run_name
    run_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (run_dir / "categories").mkdir(exist_ok=True)
    (run_dir / "products").mkdir(exist_ok=True)
    (run_dir / "screenshots").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "reports").mkdir(exist_ok=True)
    
    return run_dir

def get_category_dir(run_dir: Path, category_slug: str) -> Path:
    """Get or create category directory"""
    category_dir = run_dir / "categories" / category_slug
    category_dir.mkdir(exist_ok=True)
    return category_dir
