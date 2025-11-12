# 3DN Scraper Template - Multi-Client Web Scraping Framework

**Version:** 1.0.0 | **Status:** Production Ready

A production-ready, client-agnostic web scraping framework designed for deploying and managing multiple client scraping projects. Built with modular architecture and configuration-driven design for maximum reusability and maintainability.

---

## 🎯 Overview

The **3DN Scraper Template** is a sophisticated web scraping framework that enables rapid deployment of scraping projects for multiple clients. Originally developed for Agar Cleaning Supplies, it has been refactored into a flexible template that can be adapted to any e-commerce or product catalog website.

### Key Principles

- **Client-Agnostic Core**: Core modules work universally across all client deployments
- **Configuration-Driven**: Client-specific logic contained in configuration files
- **Strategy Pattern**: CSS selectors and extraction logic separated by client
- **Production Ready**: Battle-tested with comprehensive error handling and logging
- **Easy Deployment**: Deploy new clients in minutes with automation scripts
- **🎯 Fully Dynamic Scraping**: Zero hardcoded data - all categories and products discovered from websites at runtime

> **Architecture Note:** The scraper uses fully dynamic discovery with no hardcoded category lists or fallback values. Categories are automatically scraped from websites, ensuring complete coverage and adaptability to website changes. See [Dynamic Scraping Architecture](docs/dynamic-scraping-architecture.md) for details.

---

## ✨ Features

### Multi-Client Architecture
- 🏢 **Multiple Client Support**: Manage unlimited client deployments from single codebase
- 🔧 **Configuration Loader**: Dynamic client configuration loading system
- 📋 **Client Templates**: Pre-configured templates for rapid deployment
- 🔄 **Hot-Swappable**: Switch between clients without code changes

### Scraping Capabilities
- 🗂️ **Hierarchical Categories**: Automatic subcategory detection and recursive scraping
- 📦 **Product Details**: Comprehensive product data extraction (name, images, descriptions, SKUs)
- 📄 **Document Handling**: PDF extraction and download (SDS, PDS, datasheets)
- 📸 **Screenshot Capture**: Page screenshots for verification and debugging
- 🧪 **Test Mode**: Limited scraping for testing and development

### Operational Features
- ⚡ **Modular Design**: Each component can run standalone or as part of workflow
- 📁 **Run Management**: Timestamped directories for organized output
- 🔄 **Resume Capability**: Checkpoint system for interrupted runs
- 📊 **Comprehensive Reporting**: Detailed statistics and download tracking
- 🛡️ **Error Resilience**: Automatic retries with exponential backoff

---

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

**Quick Start with Docker:**

```bash
# 1. Create environment file
cp docker/.env.template .env

# 2. Start services (pulls Crawl4AI image, builds scraper)
docker-compose up -d

# 3. Run test scrape
docker-compose run --rm agar-scraper python main.py --client agar --test

# 4. Check results
ls -la agar_scrapes/
```

**📘 See [Docker Quick Start Guide](docs/quickstart/DOCKER_QUICKSTART.md) for full instructions**

### Option 2: Local Installation

**Prerequisites:**

```bash
# Python 3.11+ required
python --version

# Install dependencies
pip install crawl4ai aiohttp
```

**Installation:**

```bash
# Clone or download the repository
git clone <repository-url>
cd 3dn-scraper-template

# Verify installation
python main.py --help
```

**First Run (Agar Example):**

```bash
# Test mode (limited scraping)
python main.py --client agar --test

# Full scraping run
python main.py --client agar --full
```

---

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

| Document | Description |
|----------|-------------|
| **[Documentation Index](docs/README.md)** | Complete documentation navigation guide |
| **[Client Deployment Guide](docs/quickstart/CLIENT_DEPLOYMENT_GUIDE.md)** | Complete guide for deploying new clients |
| **[Configuration Guide](docs/quickstart/configuration-guide.md)** | Configuration reference and examples |
| **[Extraction Strategies](docs/architecture/extraction-strategies.md)** | CSS selector guide and testing workflows |
| **[API Reference](docs/api/api-reference.md)** | Complete API documentation for all modules |
| **[Architecture Guide](docs/architecture/architecture.md)** | System architecture and design patterns |
| **[Troubleshooting](docs/quickstart/troubleshooting.md)** | Common issues and solutions |

---

## 🏗️ Architecture

```
3DN Scraper Template
│
├── config/                      # Configuration system
│   ├── base_config.py          # Base configuration class
│   ├── config_loader.py        # Dynamic client loader
│   └── clients/                # Client deployments
│       ├── agar/               # Example: Agar client
│       │   ├── client_config.py
│       │   └── extraction_strategies.py
│       └── example_client/     # Template for new clients
│
├── core/                        # Core scraping modules
│   ├── category_scraper.py     # Category discovery
│   ├── product_collector.py    # Product URL collection
│   ├── product_scraper.py      # Product detail extraction
│   ├── product_pdf_scraper.py  # PDF link extraction
│   ├── pdf_downloader.py       # PDF file download
│   └── utils.py                # Shared utilities
│
├── strategies/                  # Strategy interfaces
│   └── base_strategy.py        # Base extraction strategy
│
├── scripts/                     # Automation scripts
│   ├── deploy_new_client.py    # Client deployment wizard
│   ├── validate_config.py      # Configuration validation
│   ├── test_connection.py      # Connection testing
│   └── test_extraction.py      # Extraction testing
│
├── docs/                        # Documentation
└── main.py                      # Main entry point
```

---

## 💼 Client Deployment

### Deploy a New Client

Use the automated deployment wizard:

```bash
python scripts/deploy_new_client.py
```

The wizard guides you through:
1. Basic client information (name, URL, categories)
2. CSS selector identification
3. Configuration file generation
4. Extraction strategy creation
5. Validation and testing

### Manual Client Creation

See the [Client Deployment Guide](docs/quickstart/CLIENT_DEPLOYMENT_GUIDE.md) for detailed instructions on:
- Creating client configuration files
- Defining extraction strategies
- Testing and validation
- Deployment best practices

---

## 🎮 Usage

### Command Line Interface

```bash
# Complete workflow with client selection
python main.py --client <client_name> [--test|--full] [options]

# Examples:
python main.py --client agar --test              # Test mode
python main.py --client agar --full              # Full run
python main.py --client myclient --full -o ./output  # Custom output

# List available clients
python main.py --list-clients

# Validate client configuration
python scripts/validate_config.py agar
```

### Modular Execution

Each core module can run independently:

```bash
# Category discovery
python -m core.category_scraper --client agar -o ./output

# Product collection
python -m core.product_collector --client agar -o ./output

# Product scraping
python -m core.product_scraper --client agar --url <product_url>

# PDF extraction
python -m core.product_pdf_scraper --client agar --products products.json

# PDF download
python -m core.pdf_downloader --run-dir <run_directory>
```

---

## 📊 Output Structure

```
<client>_scrapes/
└── <Client>Scrape_20251105_120000/
    ├── run_metadata.json          # Run information
    ├── categories.json             # All categories
    ├── all_products_list.json     # All product URLs
    ├── all_products_data.json     # All scraped products
    ├── categories/
    │   └── [category-slug]/
    │       ├── subcategories.json  # If hierarchical
    │       ├── products_list.json
    │       └── [subcategory-slug]/ # Nested structure
    ├── products/                   # Individual product JSON
    ├── pdfs/                       # PDF metadata
    ├── PDFs/                       # Downloaded PDFs
    │   └── [product]/
    │       ├── [product]_SDS.pdf
    │       └── [product]_PDS.pdf
    ├── screenshots/                # Page screenshots
    ├── logs/                       # Checkpoints
    └── reports/
        ├── final_report.json
        └── pdf_download_report.json
```

---

## 🔧 Configuration

### Client Configuration Structure

```python
# config/clients/myclient/client_config.py
from config.base_config import BaseConfig

class ClientConfig(BaseConfig):
    CLIENT_NAME = "myclient"
    CLIENT_FULL_NAME = "My Client Company"
    BASE_URL = "https://myclient.com"
    
    CATEGORY_URL_PATTERN = f"{BASE_URL}/category/{{slug}}/"
    PRODUCT_URL_PATTERN = f"{BASE_URL}/product/{{slug}}/"
    
    OUTPUT_PREFIX = "myclient"
    
    # Categories are discovered dynamically from the website
    # No manual category lists needed
```

### Extraction Strategies

```python
# config/clients/myclient/extraction_strategies.py
class MyclientExtractionStrategy:
    @staticmethod
    def get_product_detail_schema():
        return {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": [
                {"name": "product_name", "selector": "h1.title", "type": "text"},
                {"name": "main_image", "selector": "img.main", "type": "attribute", "attribute": "src"},
                # ... more fields
            ]
        }
```

See [Configuration Guide](docs/quickstart/configuration-guide.md) for complete details.

---

## 📦 Example: Agar Client

The Agar Cleaning Supplies deployment serves as a reference implementation:

```bash
# Run Agar scraper
python main.py --client agar --full

# Test Agar extraction
python scripts/test_extraction.py agar

# Validate Agar configuration
python scripts/validate_config.py agar
```

### Agar Features

- **Products**: 500+ cleaning products
- **Categories**: 50+ categories with 3-level hierarchy
- **Documents**: SDS and PDS PDF extraction and download
- **Images**: Product screenshots for verification
- **Validation**: 24/24 configuration checks passing

---

## 🛠️ Development

### Adding Custom Features

1. **Custom Extraction Logic**: Override methods in extraction strategy class
2. **Additional Fields**: Extend product schema in client configuration
3. **Custom Processing**: Add methods to core modules (maintain backward compatibility)
4. **Client-Specific Tools**: Create in `config/clients/<client>/` directory

### Testing

```bash
# Test client connection
python scripts/test_connection.py <client_name>

# Test extraction strategies
python scripts/test_extraction.py <client_name>

# Validate configuration
python scripts/validate_config.py <client_name>

# Run in test mode
python main.py --client <client_name> --test
```

---

## 📈 Performance

- **Rate Limiting**: Configurable delays between requests (2-5 seconds default)
- **Concurrent Processing**: Async operations where applicable
- **Cache Management**: Bypass caching for fresh data
- **Timeout Handling**: Configurable timeouts per page type
- **Error Recovery**: Automatic retries with exponential backoff
- **Resource Management**: Proper cleanup and connection pooling

---

## 🚨 Error Handling

- ✅ Automatic retries with different extraction strategies
- ✅ Checkpoint saving for resume capability
- ✅ Detailed error logging with context
- ✅ Graceful interruption handling (Ctrl+C)
- ✅ Configuration validation before execution
- ✅ Connection testing before scraping

---

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No products found | Site structure changed - update extraction strategies |
| Timeout errors | Increase PAGE_TIMEOUT in client config |
| Rate limiting | Adjust RATE_LIMIT_MIN/MAX in client config |
| PDF download failures | Check network, increase retries/timeout |
| Configuration errors | Run `validate_config.py` for detailed diagnostics |

See [Troubleshooting Guide](docs/quickstart/troubleshooting.md) for comprehensive solutions.

---

## 📋 Requirements

- Python 3.11+
- crawl4ai library
- aiohttp library
- asyncio support

```bash
pip install crawl4ai aiohttp
```

---

## 🤝 Contributing

### Client Contributions

To share a new client deployment:
1. Create client configuration and strategies
2. Test thoroughly with validation scripts
3. Document any client-specific quirks
4. Submit with example run output

### Core Framework Improvements

- Maintain backward compatibility
- Add unit tests for new features
- Update relevant documentation
- Follow existing code style

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-05 | Multi-client template release |
| 0.9.0 | 2025-10-31 | Agar scraper refactoring |
| 0.5.0 | 2025-10-15 | Initial Agar scraper |

---

## 🔗 Related Projects

- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Core scraping engine
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [aiohttp](https://docs.aiohttp.org/) - Async HTTP client

---

## 📄 License

For internal use only. Respect website terms of service and robots.txt when deploying to new clients.

---

## 🙏 Acknowledgments

- Built with [Crawl4AI](https://github.com/unclecode/crawl4ai)
- Inspired by modular scraping architectures
- Developed and tested with Agar Cleaning Supplies deployment

---

## 📞 Support

- 📖 [Documentation Index](docs/README.md)
- 🐛 [Troubleshooting Guide](docs/quickstart/troubleshooting.md)
- 💬 [API Reference](docs/api/api-reference.md)
- 🚀 [Deployment Guide](docs/quickstart/CLIENT_DEPLOYMENT_GUIDE.md)

---

**Happy Scraping! 🚀**
