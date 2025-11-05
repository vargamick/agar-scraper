#!/usr/bin/env python3
"""
3DN Scraper Template - Client Deployment Script

Interactive script to deploy the 3DN Scraper Template for a new client.
This script:
- Prompts for client information
- Creates client directory structure
- Generates starter configuration files
- Sets up client-specific output directories
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def prompt_with_default(prompt_text, default_value=""):
    """Prompt user with a default value."""
    if default_value:
        user_input = input(f"{prompt_text} [{default_value}]: ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt_text}: ").strip()


def validate_client_name(client_name):
    """Validate client name format."""
    if not client_name:
        return False, "Client name cannot be empty"
    
    if not client_name.islower():
        return False, "Client name must be lowercase"
    
    if " " in client_name:
        return False, "Client name cannot contain spaces (use underscores)"
    
    if not client_name.replace("_", "").isalnum():
        return False, "Client name must contain only letters, numbers, and underscores"
    
    return True, ""


def validate_url(url):
    """Validate URL format."""
    if not url:
        return False, "URL cannot be empty"
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"
    
    return True, ""


def create_client_directory(client_name, project_root):
    """Create client directory structure."""
    client_dir = project_root / "config" / "clients" / client_name
    
    if client_dir.exists():
        print(f"\n⚠️  Warning: Client directory already exists: {client_dir}")
        overwrite = input("Do you want to overwrite? (yes/no): ").strip().lower()
        if overwrite != "yes":
            print("Deployment cancelled.")
            return None
    
    # Create directory
    client_dir.mkdir(parents=True, exist_ok=True)
    
    return client_dir


def create_init_file(client_dir):
    """Create __init__.py file."""
    init_file = client_dir / "__init__.py"
    content = '"""Client configuration package."""\n'
    init_file.write_text(content)
    print(f"✓ Created {init_file.name}")


def create_client_config(client_dir, client_info):
    """Create client_config.py from template."""
    config_file = client_dir / "client_config.py"
    
    # Read template
    template_path = client_dir.parent.parent / "client_config.template.py"
    if not template_path.exists():
        print(f"⚠️  Warning: Template not found: {template_path}")
        print("Creating basic configuration...")
        template_content = """\"\"\"
3DN Scraper Template - Client Deployment Configuration
Client: {client_full_name}
Created: {date}
\"\"\"

from config.base_config import BaseConfig
from typing import Dict, List, Optional


class ClientConfig(BaseConfig):
    \"\"\"Client-specific configuration.\"\"\"
    
    # Client identification
    CLIENT_NAME = "{client_name}"
    CLIENT_FULL_NAME = "{client_full_name}"
    
    # Website configuration
    BASE_URL = "{base_url}"
    
    # URL patterns
    CATEGORY_URL_PATTERN = "{category_pattern}"
    PRODUCT_URL_PATTERN = "{product_pattern}"
    
    # Output configuration
    OUTPUT_PREFIX = "{output_prefix}"
    BASE_OUTPUT_DIR = "{output_dir}"
    
    # Known categories (update after discovery)
    KNOWN_CATEGORIES = []
    
    # PDF configuration (update based on client website)
    HAS_SDS_DOCUMENTS = False
    HAS_PDS_DOCUMENTS = False
    SDS_FIELD_NAME = "sds_url"
    PDS_FIELD_NAME = "pds_url"
    
    # Product schema mapping
    PRODUCT_SCHEMA = {{
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "product_image_url",
        "description_field": "product_description",
    }}
"""
    else:
        template_content = template_path.read_text()
    
    # Replace placeholders
    content = template_content.format(
        client_name=client_info['client_name'],
        client_full_name=client_info['client_full_name'],
        base_url=client_info['base_url'],
        category_pattern=client_info['category_pattern'],
        product_pattern=client_info['product_pattern'],
        output_prefix=client_info['output_prefix'],
        output_dir=client_info['output_dir'],
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    config_file.write_text(content)
    print(f"✓ Created {config_file.name}")


def create_extraction_strategies(client_dir, client_info):
    """Create extraction_strategies.py from template."""
    strategies_file = client_dir / "extraction_strategies.py"
    
    content = f'''"""
3DN Scraper Template - Extraction Strategies
Client: {client_info['client_full_name']}
Created: {datetime.now().strftime("%Y-%m-%d")}

NOTE: You need to update the selectors below based on the client's website structure.
Use browser developer tools to inspect the HTML and identify the correct CSS selectors.
"""

from typing import Dict, List, Optional
from strategies.base_strategy import ExtractionStrategy


class ClientExtractionStrategy(ExtractionStrategy):
    """Client-specific CSS selectors and extraction logic."""
    
    # Category page selectors
    # TODO: Update these selectors based on client website
    CATEGORY_SELECTORS = {{
        "products": "ul.products li.product",  # Selector for product list items
        "product_link": "a.product-link",      # Selector for product URLs
        "product_name": "h2.product-title",    # Selector for product names
        "pagination": "a.next-page"            # Optional: Selector for pagination
    }}
    
    # Product detail page selectors
    # TODO: Update these selectors based on client website
    PRODUCT_SELECTORS = {{
        "name": "h1.product-title",           # Product name
        "image": "img.product-image",         # Main product image
        "description": "div.description",     # Product description
        "overview": "div.overview",           # Product overview (if separate)
        "sku": "span.sku",                    # SKU/Product code (optional)
        "categories": "a.category",           # Product categories (optional)
        "price": "span.price"                 # Product price (optional)
    }}
    
    # PDF/Document link selectors (if applicable)
    # TODO: Update these if client has downloadable documents
    PDF_SELECTORS = {{
        "sds_link": "a[href*='SDS']",         # Safety Data Sheet link
        "pds_link": "a[href*='PDS']",         # Product Data Sheet link
        "document_section": "div.documents"   # Section containing documents
    }}
    
    def extract_category_products(self, html: str) -> List[Dict]:
        """
        Extract product information from category page.
        
        Override this method if you need custom extraction logic
        beyond basic CSS selection.
        """
        # Default implementation uses CSS selectors
        # Override if needed for complex extraction
        return super().extract_category_products(html)
    
    def extract_product_details(self, html: str) -> Dict:
        """
        Extract detailed product information from product page.
        
        Override this method if you need custom extraction logic
        beyond basic CSS selection.
        """
        # Default implementation uses CSS selectors
        # Override if needed for complex extraction
        return super().extract_product_details(html)
    
    def extract_pdf_links(self, html: str) -> Dict:
        """
        Extract PDF/document links from product page.
        
        Override this method if you need custom extraction logic
        beyond basic CSS selection.
        """
        # Default implementation uses CSS selectors
        # Override if needed for complex extraction
        return super().extract_pdf_links(html)


# Helper functions for custom extraction logic
def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    return text.strip()


def extract_price(price_text: str) -> Optional[float]:
    """Extract numeric price from text."""
    if not price_text:
        return None
    
    # Remove currency symbols and convert to float
    import re
    price_str = re.sub(r'[^0-9.]', '', price_text)
    try:
        return float(price_str)
    except ValueError:
        return None


def extract_sku(sku_text: str) -> str:
    """Extract SKU from text."""
    if not sku_text:
        return ""
    
    # Remove common prefixes like "SKU:", "Code:", etc.
    import re
    return re.sub(r'^(SKU|Code|Item):\\s*', '', sku_text, flags=re.IGNORECASE).strip()
'''
    
    strategies_file.write_text(content)
    print(f"✓ Created {strategies_file.name}")


def create_output_directory(client_info, project_root):
    """Create output directory structure."""
    output_dir = project_root / client_info['output_dir']
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Created output directory: {output_dir}")


def create_readme(client_dir, client_info):
    """Create README for client deployment."""
    readme_file = client_dir / "README.md"
    
    content = f'''# {client_info['client_full_name']} - 3DN Scraper Deployment

**Client:** {client_info['client_full_name']}  
**Website:** {client_info['base_url']}  
**Created:** {datetime.now().strftime("%Y-%m-%d")}

## Configuration Status

- [x] Basic configuration created
- [ ] URL patterns validated
- [ ] Extraction selectors configured
- [ ] Test extraction completed
- [ ] Full scrape validated

## Next Steps

1. **Validate Configuration:**
   ```bash
   python scripts/validate_config.py --client {client_info['client_name']}
   ```

2. **Test Connection:**
   ```bash
   python scripts/test_connection.py --client {client_info['client_name']}
   ```

3. **Configure Extraction Selectors:**
   - Open `extraction_strategies.py`
   - Use browser dev tools to inspect client website
   - Update CSS selectors for category and product pages
   - Save changes

4. **Test Extraction:**
   ```bash
   python scripts/test_extraction.py --client {client_info['client_name']} --url "sample-product-url"
   ```

5. **Run Test Scrape:**
   ```bash
   python main.py --client {client_info['client_name']} --test
   ```

6. **Iterate and Refine:**
   - Review test output
   - Adjust selectors as needed
   - Re-test until extraction is accurate

7. **Full Deployment:**
   ```bash
   python main.py --client {client_info['client_name']}
   ```

## Configuration Files

- `client_config.py` - Client-specific configuration
- `extraction_strategies.py` - CSS selectors and extraction logic

## Notes

Add any client-specific notes here:
- Special requirements
- Known issues
- Contact information
- Access credentials location (if needed)
'''
    
    readme_file.write_text(content)
    print(f"✓ Created {readme_file.name}")


def main():
    """Main deployment workflow."""
    print("=" * 80)
    print("3DN Scraper Template - New Client Deployment")
    print("=" * 80)
    print()
    
    project_root = get_project_root()
    
    # Collect client information
    print("Please provide the following information about the new client:\n")
    
    # Client name
    while True:
        client_name = prompt_with_default(
            "Client short name (lowercase, no spaces)",
            ""
        )
        valid, error = validate_client_name(client_name)
        if valid:
            break
        print(f"❌ {error}")
    
    # Client full name
    client_full_name = prompt_with_default(
        "Client full name",
        client_name.replace("_", " ").title()
    )
    
    # Base URL
    while True:
        base_url = prompt_with_default(
            "Client website URL",
            f"https://{client_name}.com"
        )
        valid, error = validate_url(base_url)
        if valid:
            break
        print(f"❌ {error}")
    
    # Remove trailing slash
    base_url = base_url.rstrip("/")
    
    # URL patterns
    category_pattern = prompt_with_default(
        "Category URL pattern (use {slug} placeholder)",
        "/category/{slug}/"
    )
    
    product_pattern = prompt_with_default(
        "Product URL pattern (use {slug} placeholder)",
        "/product/{slug}/"
    )
    
    # Output configuration
    output_prefix_default = f"{client_name.title().replace('_', '')}Scrape"
    output_prefix = prompt_with_default(
        "Output directory prefix",
        output_prefix_default
    )
    
    output_dir = prompt_with_default(
        "Base output directory",
        f"{client_name}_scrapes"
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("Deployment Summary:")
    print("=" * 80)
    print(f"Client Name:          {client_name}")
    print(f"Client Full Name:     {client_full_name}")
    print(f"Website URL:          {base_url}")
    print(f"Category Pattern:     {category_pattern}")
    print(f"Product Pattern:      {product_pattern}")
    print(f"Output Prefix:        {output_prefix}")
    print(f"Output Directory:     {output_dir}")
    print("=" * 80)
    print()
    
    # Confirm
    confirm = input("Proceed with deployment? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deployment cancelled.")
        return
    
    # Store client info
    client_info = {
        'client_name': client_name,
        'client_full_name': client_full_name,
        'base_url': base_url,
        'category_pattern': category_pattern,
        'product_pattern': product_pattern,
        'output_prefix': output_prefix,
        'output_dir': output_dir
    }
    
    # Create deployment
    print("\nCreating client deployment...\n")
    
    try:
        # Create client directory
        client_dir = create_client_directory(client_name, project_root)
        if not client_dir:
            return
        
        # Create files
        create_init_file(client_dir)
        create_client_config(client_dir, client_info)
        create_extraction_strategies(client_dir, client_info)
        create_readme(client_dir, client_info)
        create_output_directory(client_info, project_root)
        
        print("\n" + "=" * 80)
        print("✅ Client deployment created successfully!")
        print("=" * 80)
        print(f"\nClient directory: {client_dir}")
        print("\nNext steps:")
        print(f"1. cd {project_root}")
        print(f"2. python scripts/validate_config.py --client {client_name}")
        print(f"3. python scripts/test_connection.py --client {client_name}")
        print(f"4. Edit {client_dir / 'extraction_strategies.py'}")
        print(f"5. python scripts/test_extraction.py --client {client_name}")
        print(f"6. python main.py --client {client_name} --test")
        print("\nSee the README in the client directory for detailed instructions.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
