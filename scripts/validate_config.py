#!/usr/bin/env python3
"""
3DN Scraper Template - Configuration Validation Script

Validates client configuration files to ensure they have all required settings
and that the settings are valid.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_client_exists(client_name: str, project_root: Path) -> Tuple[bool, str]:
    """Check if client directory exists."""
    client_dir = project_root / "config" / "clients" / client_name
    if not client_dir.exists():
        return False, f"Client directory not found: {client_dir}"
    
    config_file = client_dir / "client_config.py"
    if not config_file.exists():
        return False, f"Client configuration file not found: {config_file}"
    
    strategies_file = client_dir / "extraction_strategies.py"
    if not strategies_file.exists():
        return False, f"Extraction strategies file not found: {strategies_file}"
    
    return True, "Client directory structure valid"


def load_client_config(client_name: str):
    """Load client configuration."""
    try:
        from config.config_loader import load_config
        config = load_config(client_name)
        return True, config, None
    except Exception as e:
        return False, None, str(e)


def validate_required_fields(config) -> List[Tuple[str, bool, str]]:
    """Validate required configuration fields."""
    results = []
    
    required_fields = {
        'CLIENT_NAME': 'Client short name identifier',
        'CLIENT_FULL_NAME': 'Client full/display name',
        'BASE_URL': 'Base website URL',
        'CATEGORY_URL_PATTERN': 'Category URL pattern',
        'PRODUCT_URL_PATTERN': 'Product URL pattern',
        'OUTPUT_PREFIX': 'Output directory prefix',
        'BASE_OUTPUT_DIR': 'Base output directory',
    }
    
    for field, description in required_fields.items():
        if hasattr(config, field):
            value = getattr(config, field)
            if value:
                results.append((field, True, f"{description}: {value}"))
            else:
                results.append((field, False, f"{description} is empty"))
        else:
            results.append((field, False, f"{description} is missing"))
    
    return results


def validate_url_format(config) -> List[Tuple[str, bool, str]]:
    """Validate URL format."""
    results = []
    
    # Check BASE_URL
    if hasattr(config, 'BASE_URL'):
        base_url = config.BASE_URL
        if base_url.startswith('http://') or base_url.startswith('https://'):
            results.append(('BASE_URL format', True, f"Valid: {base_url}"))
        else:
            results.append(('BASE_URL format', False, f"Must start with http:// or https://: {base_url}"))
    
    # Check URL patterns contain {slug}
    if hasattr(config, 'CATEGORY_URL_PATTERN'):
        pattern = config.CATEGORY_URL_PATTERN
        if '{slug}' in pattern:
            results.append(('CATEGORY_URL_PATTERN', True, f"Contains {{slug}}: {pattern}"))
        else:
            results.append(('CATEGORY_URL_PATTERN', False, f"Must contain {{slug}} placeholder: {pattern}"))
    
    if hasattr(config, 'PRODUCT_URL_PATTERN'):
        pattern = config.PRODUCT_URL_PATTERN
        if '{slug}' in pattern:
            results.append(('PRODUCT_URL_PATTERN', True, f"Contains {{slug}}: {pattern}"))
        else:
            results.append(('PRODUCT_URL_PATTERN', False, f"Must contain {{slug}} placeholder: {pattern}"))
    
    return results


def validate_output_config(config, project_root: Path) -> List[Tuple[str, bool, str]]:
    """Validate output configuration."""
    results = []
    
    # Check output directory
    if hasattr(config, 'BASE_OUTPUT_DIR'):
        output_dir = project_root / config.BASE_OUTPUT_DIR
        if output_dir.exists():
            results.append(('Output directory', True, f"Exists: {output_dir}"))
        else:
            results.append(('Output directory', False, f"Does not exist (will be created on first run): {output_dir}"))
    
    # Check output prefix is valid
    if hasattr(config, 'OUTPUT_PREFIX'):
        prefix = config.OUTPUT_PREFIX
        if prefix and not any(c in prefix for c in [' ', '/', '\\']):
            results.append(('Output prefix', True, f"Valid: {prefix}"))
        else:
            results.append(('Output prefix', False, f"Invalid (contains spaces or path separators): {prefix}"))
    
    return results


def validate_pdf_config(config) -> List[Tuple[str, bool, str]]:
    """Validate PDF configuration."""
    results = []
    
    if hasattr(config, 'HAS_SDS_DOCUMENTS'):
        has_sds = config.HAS_SDS_DOCUMENTS
        results.append(('SDS Documents', True, f"{'Enabled' if has_sds else 'Disabled'}"))
        
        if has_sds and hasattr(config, 'SDS_FIELD_NAME'):
            results.append(('SDS Field Name', True, f"Set to: {config.SDS_FIELD_NAME}"))
        elif has_sds:
            results.append(('SDS Field Name', False, "Missing (required when SDS enabled)"))
    
    if hasattr(config, 'HAS_PDS_DOCUMENTS'):
        has_pds = config.HAS_PDS_DOCUMENTS
        results.append(('PDS Documents', True, f"{'Enabled' if has_pds else 'Disabled'}"))
        
        if has_pds and hasattr(config, 'PDS_FIELD_NAME'):
            results.append(('PDS Field Name', True, f"Set to: {config.PDS_FIELD_NAME}"))
        elif has_pds:
            results.append(('PDS Field Name', False, "Missing (required when PDS enabled)"))
    
    return results


def validate_schema_mapping(config) -> List[Tuple[str, bool, str]]:
    """Validate product schema mapping."""
    results = []
    
    if hasattr(config, 'PRODUCT_SCHEMA'):
        schema = config.PRODUCT_SCHEMA
        if isinstance(schema, dict):
            results.append(('Product schema', True, f"Defined with {len(schema)} fields"))
            
            # Check common fields
            common_fields = ['name_field', 'url_field', 'description_field']
            for field in common_fields:
                if field in schema:
                    results.append((f"Schema: {field}", True, f"Mapped to: {schema[field]}"))
                else:
                    results.append((f"Schema: {field}", False, f"Missing (recommended)"))
        else:
            results.append(('Product schema', False, "Must be a dictionary"))
    else:
        results.append(('Product schema', False, "Not defined (required)"))
    
    return results


def validate_extraction_strategies(client_name: str, project_root: Path) -> List[Tuple[str, bool, str]]:
    """Validate extraction strategies file."""
    results = []
    
    strategies_file = project_root / "config" / "clients" / client_name / "extraction_strategies.py"
    
    if not strategies_file.exists():
        results.append(('Extraction strategies', False, "File not found"))
        return results
    
    # Read file content
    content = strategies_file.read_text()
    
    # Check for TODO markers (indicates incomplete configuration)
    todo_count = content.count('TODO:')
    if todo_count > 0:
        results.append(('Extraction strategies', False, f"Contains {todo_count} TODO markers - selectors need to be configured"))
    else:
        results.append(('Extraction strategies', True, "No TODO markers found"))
    
    # Check for required selector definitions
    required_selectors = ['CATEGORY_SELECTORS', 'PRODUCT_SELECTORS']
    for selector in required_selectors:
        if selector in content:
            results.append((f"Selectors: {selector}", True, "Defined"))
        else:
            results.append((f"Selectors: {selector}", False, "Missing (required)"))
    
    # Check for PDF selectors if needed
    if 'PDF_SELECTORS' in content:
        results.append(('Selectors: PDF_SELECTORS', True, "Defined"))
    
    return results


def print_results(results: List[Tuple[str, bool, str]], category: str):
    """Print validation results."""
    print(f"\n{category}:")
    print("-" * 80)
    
    for field, valid, message in results:
        status = "✓" if valid else "✗"
        color = "\033[92m" if valid else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset} {field}: {message}")


def main():
    """Main validation workflow."""
    parser = argparse.ArgumentParser(
        description='Validate 3DN Scraper Template client configuration'
    )
    parser.add_argument(
        '--client',
        required=True,
        help='Client name to validate'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed validation information'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"3DN Scraper Template - Configuration Validation")
    print(f"Client: {args.client}")
    print("=" * 80)
    
    project_root = Path(__file__).parent.parent
    
    # Check client exists
    exists, message = validate_client_exists(args.client, project_root)
    if not exists:
        print(f"\n✗ {message}")
        sys.exit(1)
    
    print(f"✓ {message}")
    
    # Load configuration
    success, config, error = load_client_config(args.client)
    if not success:
        print(f"\n✗ Failed to load configuration: {error}")
        sys.exit(1)
    
    print("✓ Configuration loaded successfully")
    
    # Run validations
    all_results = []
    
    # Required fields
    results = validate_required_fields(config)
    all_results.extend(results)
    print_results(results, "Required Fields")
    
    # URL format
    results = validate_url_format(config)
    all_results.extend(results)
    print_results(results, "URL Configuration")
    
    # Output configuration
    results = validate_output_config(config, project_root)
    all_results.extend(results)
    print_results(results, "Output Configuration")
    
    # PDF configuration
    results = validate_pdf_config(config)
    all_results.extend(results)
    if results:  # Only show if PDF config exists
        print_results(results, "PDF Configuration")
    
    # Schema mapping
    results = validate_schema_mapping(config)
    all_results.extend(results)
    print_results(results, "Schema Mapping")
    
    # Extraction strategies
    results = validate_extraction_strategies(args.client, project_root)
    all_results.extend(results)
    print_results(results, "Extraction Strategies")
    
    # Summary
    print("\n" + "=" * 80)
    total = len(all_results)
    passed = sum(1 for _, valid, _ in all_results if valid)
    failed = total - passed
    
    print(f"Validation Summary:")
    print(f"  Total checks: {total}")
    print(f"  Passed: \033[92m{passed}\033[0m")
    print(f"  Failed: \033[91m{failed}\033[0m")
    
    if failed == 0:
        print("\n✅ All validation checks passed!")
        print("\nNext steps:")
        print(f"  1. python scripts/test_connection.py --client {args.client}")
        print(f"  2. Configure extraction selectors in extraction_strategies.py")
        print(f"  3. python scripts/test_extraction.py --client {args.client}")
        print(f"  4. python main.py --client {args.client} --test")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n⚠️  Some validation checks failed. Please review and fix the issues above.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
