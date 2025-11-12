# 3DN Scraper Template - Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2025-01-11  
**Template Version:** 1.0.0

---

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Configuration Issues](#configuration-issues)
3. [Connection Issues](#connection-issues)
4. [Extraction Issues](#extraction-issues)
5. [Scraping Issues](#scraping-issues)
6. [PDF Download Issues](#pdf-download-issues)
7. [Performance Issues](#performance-issues)
8. [Environment Issues](#environment-issues)
9. [Common Error Messages](#common-error-messages)
10. [Getting Additional Help](#getting-additional-help)

---

## Quick Diagnostic Checklist

Before diving into detailed troubleshooting, run through this quick checklist:

### Basic Checks

- [ ] **Python version:** Python 3.11+ installed? (`python --version`)
- [ ] **Virtual environment:** Is venv activated? (should see `(venv)` in terminal)
- [ ] **Dependencies:** All packages installed? (`pip list | grep crawl4ai`)
- [ ] **Configuration:** Validation passes? (`python scripts/validate_config.py --client NAME`)
- [ ] **Connection:** Website accessible? (`python scripts/test_connection.py --client NAME`)
- [ ] **Permissions:** Can write to output directory?

### Quick Tests

```bash
# 1. Validate configuration
python scripts/validate_config.py --client clientname

# 2. Test website connection
python scripts/test_connection.py --client clientname

# 3. Test extraction on sample URL
python scripts/test_extraction.py --client clientname --url "URL"

# 4. Run test mode scrape
python main.py --client clientname --test
```

### Log Files

Check these locations for error details:

```
{client}_scrapes/run_YYYYMMDD_HHMMSS/logs/
├── scraper.log           # Main scraping log
├── errors.log            # Error-only log
└── debug.log             # Detailed debug info
```

---

## Configuration Issues

### Issue: Client Configuration Not Found

**Error Message:**
```
ConfigError: Client configuration not found for 'clientname'
```

**Causes:**
- Client directory doesn't exist
- Typo in client name
- Missing `__init__.py` files

**Solutions:**

1. **Verify directory exists:**
   ```bash
   ls -la config/clients/clientname/
   ```
   Should show:
   - `__init__.py`
   - `client_config.py`
   - `extraction_strategies.py`

2. **Check client name spelling:**
   ```bash
   # List available clients
   ls config/clients/
   ```

3. **Re-create client if needed:**
   ```bash
   python scripts/deploy_new_client.py
   ```

---

### Issue: Required Field Missing

**Error Message:**
```
ConfigError: Required field 'BASE_URL' not found in client configuration
```

**Causes:**
- Field not defined in `client_config.py`
- Field has typo
- Not inheriting from `BaseConfig`

**Solutions:**

1. **Check inheritance:**
   ```python
   # client_config.py must inherit BaseConfig
   from config.base_config import BaseConfig
   
   class ClientConfig(BaseConfig):  # Must inherit
       # fields here
   ```

2. **Add missing field:**
   ```python
   class ClientConfig(BaseConfig):
       CLIENT_NAME = "clientname"
       CLIENT_FULL_NAME = "Client Company"
       BASE_URL = "https://client.com"  # Add this
       # ... other required fields
   ```

3. **Run validation:**
   ```bash
   python scripts/validate_config.py --client clientname
   ```
   This will show all missing required fields.

---

### Issue: Invalid URL Pattern

**Error Message:**
```
ConfigError: URL pattern must contain {slug} placeholder
```

**Causes:**
- Missing `{slug}` in pattern
- Typo in placeholder

**Solutions:**

```python
# Wrong
CATEGORY_URL_PATTERN = "/category/"
PRODUCT_URL_PATTERN = "/product/"

# Correct
CATEGORY_URL_PATTERN = "/category/{slug}/"
PRODUCT_URL_PATTERN = "/product/{slug}/"
```

---

### Issue: Configuration Validation Fails

**Symptoms:**
- Multiple validation checks fail
- Can't proceed with scraping

**Solutions:**

1. **Review all errors:**
   ```bash
   python scripts/validate_config.py --client clientname
   ```
   Fix errors one by one from top to bottom.

2. **Compare with working example:**
   ```bash
   # View Agar configuration as reference
   cat config/clients/agar/client_config.py
   ```

3. **Start fresh if needed:**
   ```bash
   # Backup existing
   mv config/clients/clientname config/clients/clientname.backup
   
   # Re-deploy
   python scripts/deploy_new_client.py
   ```

---

## Connection Issues

### Issue: Cannot Connect to Website

**Error Message:**
```
ConnectionError: Failed to connect to https://client.com
```

**Causes:**
- Website down or unreachable
- Incorrect URL
- Firewall/proxy blocking
- SSL certificate issues

**Solutions:**

1. **Test in browser:**
   - Open URL in browser
   - Verify it loads successfully
   - Check for redirects

2. **Check URL format:**
   ```python
   # Must include protocol
   BASE_URL = "https://client.com"  # Correct
   BASE_URL = "client.com"          # Wrong - missing https://
   ```

3. **Test connection:**
   ```bash
   python scripts/test_connection.py --client clientname --base-only
   ```

4. **Check for SSL issues:**
   ```bash
   # If SSL certificate error
   curl -v https://client.com
   ```
   If certificate is invalid, you may need to configure SSL verification bypass (not recommended for production).

5. **Test with curl:**
   ```bash
   curl -I https://client.com
   ```
   Should return `200 OK` status.

---

### Issue: DNS Resolution Failed

**Error Message:**
```
DNSError: Failed to resolve hostname client.com
```

**Causes:**
- Domain doesn't exist
- Typo in domain name
- DNS server issues

**Solutions:**

1. **Verify domain:**
   ```bash
   nslookup client.com
   dig client.com
   ```

2. **Check for typos:**
   ```python
   BASE_URL = "https://client.com"  # Check spelling
   ```

3. **Try alternative DNS:**
   ```bash
   # Use Google DNS temporarily
   networksetup -setdnsservers Wi-Fi 8.8.8.8
   ```

---

### Issue: Connection Timeout

**Error Message:**
```
TimeoutError: Request timed out after 60000ms
```

**Causes:**
- Website slow to respond
- Network issues
- Timeout too short

**Solutions:**

1. **Increase timeout:**
   ```python
   # client_config.py
   class ClientConfig(BaseConfig):
       PAGE_TIMEOUT = 120000  # 120 seconds
       DETAIL_PAGE_TIMEOUT = 90000  # 90 seconds
   ```

2. **Check network:**
   ```bash
   ping client.com
   # Should show response times
   ```

3. **Test specific URL:**
   ```bash
   time curl -I https://client.com
   # Shows how long request takes
   ```

---

### Issue: 403 Forbidden / 429 Too Many Requests

**Error Message:**
```
HTTPError: 403 Forbidden
HTTPError: 429 Too Many Requests
```

**Causes:**
- Rate limiting
- Bot detection
- User agent blocking
- IP blocking

**Solutions:**

1. **Increase rate limit delay:**
   ```python
   # client_config.py
   class ClientConfig(BaseConfig):
       RATE_LIMIT_DELAY = 10  # 10 seconds between requests
   ```

2. **Check User-Agent:**
   ```python
   # Verify user agent is set
   USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
   ```

3. **Reduce concurrent requests:**
   ```python
   # Reduce load on server
   TEST_CATEGORY_LIMIT = 1
   TEST_PRODUCT_LIMIT = 3
   ```

4. **Wait before retrying:**
   - Stop scraping temporarily
   - Wait 15-30 minutes
   - Resume with increased delays

---

## Extraction Issues

### Issue: No Products Found on Category Page

**Error Message:**
```
Found 0 products on category page
```

**Causes:**
- Wrong selector
- JavaScript-rendered content
- Empty category
- Page structure changed

**Solutions:**

1. **Test selector in browser:**
   ```javascript
   // Open category page, press F12, console:
   document.querySelectorAll("YOUR_PRODUCTS_SELECTOR")
   // Should return array of products
   ```

2. **Check page has products:**
   - Verify category has products in browser
   - Try different category

3. **Update selectors:**
   ```python
   # extraction_strategies.py
   CATEGORY_SELECTORS = {
       "products": "NEW_SELECTOR_HERE"
   }
   ```

4. **Test extraction:**
   ```bash
   python scripts/test_extraction.py \
       --client clientname \
       --url "CATEGORY_URL" \
       --type category
   ```

5. **Save HTML for inspection:**
   ```bash
   python scripts/test_extraction.py \
       --client clientname \
       --url "CATEGORY_URL" \
       --save
   ```

---

### Issue: Product Field Extraction Fails

**Error Message:**
```
Failed to extract field 'name' from product page
```

**Causes:**
- Incorrect selector
- Field doesn't exist on this product
- HTML structure different

**Solutions:**

1. **Test selector in browser:**
   ```javascript
   // On product page, F12 console:
   document.querySelector("YOUR_SELECTOR")
   // Should return the element
   ```

2. **Check if optional field:**
   ```python
   # Some fields may not exist on all products
   # This is OK for optional fields like SKU, categories
   ```

3. **Update selector:**
   ```python
   # extraction_strategies.py
   PRODUCT_SELECTORS = {
       "name": "NEW_SELECTOR_HERE"
   }
   ```

4. **Test on multiple products:**
   ```bash
   # Test on different product URLs
   python scripts/test_extraction.py --client clientname --url "URL1"
   python scripts/test_extraction.py --client clientname --url "URL2"
   ```

---

### Issue: Extracting Wrong Content

**Symptoms:**
- Getting unrelated text
- Getting multiple values concatenated
- Getting HTML instead of text

**Solutions:**

1. **Make selector more specific:**
   ```python
   # Too generic
   "name": "h1"
   
   # More specific
   "name": "div.product h1.product-title"
   
   # Very specific
   "name": "main article.product header h1.title"
   ```

2. **Use unique identifiers:**
   ```python
   # Prefer specific classes
   "name": "h1.product-title"
   
   # Or data attributes
   "name": "h1[data-product-name]"
   ```

3. **Test selector isolation:**
   ```javascript
   // Should return only one element
   document.querySelectorAll("YOUR_SELECTOR").length  // Should be 1
   ```

---

### Issue: Selectors Work on Some Pages But Not Others

**Symptoms:**
- Extraction succeeds on test page
- Fails on other product/category pages
- Inconsistent results

**Solutions:**

1. **Test on multiple pages:**
   ```bash
   # Test various URLs
   for url in url1 url2 url3; do
       python scripts/test_extraction.py --client clientname --url "$url"
   done
   ```

2. **Find common patterns:**
   - Inspect HTML of working vs failing pages
   - Find selectors that work across all pages

3. **Use more stable selectors:**
   ```python
   # Avoid position-dependent selectors
   "name": "div:nth-child(3) h1"  # BAD - depends on position
   
   # Use class-based selectors
   "name": "h1.product-title"     # GOOD - stable
   ```

4. **Handle variations:**
   ```python
   # Multiple possible selectors
   "name": "h1.product-title, h2.product-title"
   ```

---

## Scraping Issues

### Issue: Scrape Hangs or Freezes

**Symptoms:**
- Script stops responding
- No progress for long time
- Memory usage keeps growing

**Solutions:**

1. **Check logs:**
   ```bash
   tail -f {client}_scrapes/run_*/logs/scraper.log
   ```

2. **Reduce scope:**
   ```python
   # Test with smaller limits
   TEST_CATEGORY_LIMIT = 1
   TEST_PRODUCT_LIMIT = 2
   ```

3. **Increase timeouts:**
   ```python
   PAGE_TIMEOUT = 120000  # Give more time
   ```

4. **Check memory:**
   ```bash
   # Monitor memory usage
   top -p $(pgrep -f "python main.py")
   ```

5. **Restart with test mode:**
   ```bash
   # Kill hanging process
   pkill -f "python main.py"
   
   # Restart in test mode
   python main.py --client clientname --test
   ```

---

### Issue: Scraping Very Slow

**Symptoms:**
- Takes much longer than expected
- Progress very slow
- High CPU/memory usage

**Solutions:**

1. **Check rate limiting:**
   ```python
   # May be too aggressive delay
   RATE_LIMIT_DELAY = 2  # Reduce if safe
   ```

2. **Check timeouts:**
   ```python
   # May be waiting too long
   PAGE_TIMEOUT = 30000  # Reduce if pages load faster
   ```

3. **Monitor network:**
   ```bash
   # Check if network is bottleneck
   iftop  # Linux
   nettop # macOS
   ```

4. **Reduce PDF downloads:**
   ```python
   # Temporarily disable PDFs
   HAS_SDS_DOCUMENTS = False
   HAS_PDS_DOCUMENTS = False
   ```

---

### Issue: Incomplete Scrape Results

**Symptoms:**
- Some products missing
- Some categories skipped
- Partial data

**Solutions:**

1. **Check logs for errors:**
   ```bash
   grep "ERROR\|WARN" {client}_scrapes/run_*/logs/scraper.log
   ```

2. **Review failed items:**
   ```bash
   grep "Failed" {client}_scrapes/run_*/logs/scraper.log
   ```

3. **Increase retries:**
   ```python
   MAX_RETRIES = 5  # More retry attempts
   RETRY_DELAY = 10  # Longer wait between retries
   ```

4. **Re-run for missing items:**
   - Note which categories/products failed
   - Run targeted scrape for those items

---

## PDF Download Issues

### Issue: PDFs Not Downloading

**Error Message:**
```
Failed to download PDF: ...
```

**Causes:**
- Incorrect selectors
- PDFs require authentication
- PDF URLs invalid
- Connection issues

**Solutions:**

1. **Verify PDF configuration:**
   ```python
   # client_config.py
   HAS_SDS_DOCUMENTS = True  # Should be True
   HAS_PDS_DOCUMENTS = True  # Should be True
   ```

2. **Test PDF selectors:**
   ```javascript
   // On product page, F12 console:
   document.querySelector("a[href*='SDS']")
   // Should return link element
   ```

3. **Check PDF URLs:**
   ```javascript
   // Get PDF URL
   let link = document.querySelector("a[href*='SDS']")
   console.log(link.href)  // Should be valid URL
   ```

4. **Test PDF download manually:**
   ```bash
   # Try downloading PDF directly
   curl -O "PDF_URL"
   ```

5. **Update PDF selectors:**
   ```python
   # extraction_strategies.py
   PDF_SELECTORS = {
       "sds_link": "NEW_SELECTOR",
       "pds_link": "NEW_SELECTOR"
   }
   ```

---

### Issue: PDF Download Timeout

**Error Message:**
```
PDFDownloadError: Download timeout after 30 seconds
```

**Solutions:**

1. **Increase PDF timeout:**
   ```python
   # client_config.py
   class ClientConfig(BaseConfig):
       PDF_TIMEOUT = 60  # 60 seconds
       PDF_MAX_RETRIES = 5
   ```

2. **Check PDF file size:**
   ```bash
   # See if PDFs are very large
   curl -I "PDF_URL" | grep "Content-Length"
   ```

3. **Test download speed:**
   ```bash
   time curl -O "PDF_URL"
   ```

---

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- Memory keeps increasing
- System becomes slow
- Out of memory errors

**Solutions:**

1. **Reduce batch size:**
   ```python
   TEST_PRODUCT_LIMIT = 5  # Process fewer products at once
   ```

2. **Clear cache regularly:**
   - Restart scraper periodically
   - Process in batches

3. **Monitor memory:**
   ```bash
   # Watch memory usage
   watch -n 1 'ps aux | grep python'
   ```

4. **Check for memory leaks:**
   - Run in test mode
   - Monitor if memory keeps growing

---

### Issue: High CPU Usage

**Symptoms:**
- CPU at 100%
- System unresponsive
- Scraping very slow

**Solutions:**

1. **Add delays:**
   ```python
   RATE_LIMIT_DELAY = 3  # Give CPU time to rest
   ```

2. **Reduce concurrency:**
   - Process one item at a time
   - Don't run multiple scrapers simultaneously

3. **Check what's consuming CPU:**
   ```bash
   top  # Linux
   Activity Monitor  # macOS
   ```

---

## Environment Issues

### Issue: Python Version Incompatible

**Error Message:**
```
Python 3.11 or higher required
```

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version
   # Should show 3.11 or higher
   ```

2. **Install Python 3.11+:**
   ```bash
   # macOS
   brew install python@3.11
   
   # Ubuntu/Debian
   sudo apt install python3.11
   ```

3. **Update virtual environment:**
   ```bash
   # Remove old venv
   rm -rf venv
   
   # Create with Python 3.11
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

### Issue: Missing Dependencies

**Error Message:**
```
ModuleNotFoundError: No module named 'crawl4ai'
```

**Solutions:**

1. **Ensure venv activated:**
   ```bash
   source venv/bin/activate  # Linux/macOS
   # Should see (venv) in prompt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   pip list | grep crawl4ai
   ```

4. **Reinstall if needed:**
   ```bash
   pip uninstall crawl4ai
   pip install crawl4ai
   ```

---

### Issue: Permission Denied

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: 'output_directory'
```

**Solutions:**

1. **Check directory permissions:**
   ```bash
   ls -la {client}_scrapes/
   ```

2. **Create directory if missing:**
   ```bash
   mkdir -p {client}_scrapes
   ```

3. **Fix permissions:**
   ```bash
   chmod 755 {client}_scrapes
   ```

4. **Check disk space:**
   ```bash
   df -h  # Linux/macOS
   ```

---

## Common Error Messages

### `ImportError: cannot import name 'ClientConfig'`

**Cause:** Syntax error in client_config.py

**Solution:**
```bash
# Check for Python syntax errors
python -m py_compile config/clients/clientname/client_config.py
```

---

### `JSONDecodeError: Expecting value`

**Cause:** Invalid JSON in output file

**Solution:**
- Check logs for errors during scraping
- Re-scrape affected products
- Verify extraction returns valid data

---

### `UnicodeDecodeError`

**Cause:** Non-UTF-8 characters in content

**Solution:**
- Usually handled automatically
- Check if special characters in product names
- Verify file encoding

---

### `ConnectionResetError`

**Cause:** Server closed connection

**Solution:**
- Increase RATE_LIMIT_DELAY
- Add retries
- Check if being rate limited

---

### `SSLError: certificate verify failed`

**Cause:** Invalid SSL certificate

**Solution:**
```python
# NOT RECOMMENDED for production
# But can help diagnose
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

---

## Getting Additional Help

### Diagnostic Information to Collect

When seeking help, provide:

1. **System Information:**
   ```bash
   python --version
   pip list | grep crawl4ai
   uname -a  # OS info
   ```

2. **Configuration:**
   ```bash
   cat config/clients/clientname/client_config.py
   cat config/clients/clientname/extraction_strategies.py
   ```

3. **Logs:**
   ```bash
   tail -100 {client}_scrapes/run_*/logs/scraper.log
   tail -100 {client}_scrapes/run_*/logs/errors.log
   ```

4. **Error Messages:**
   - Full error message and stack trace
   - When error occurs
   - Steps to reproduce

### Debug Mode

Enable verbose logging:

```python
# client_config.py or .env
LOG_LEVEL = "DEBUG"
```

```bash
# Run with debug output
python main.py --client clientname --test 2>&1 | tee debug.log
```

### Useful Commands

```bash
# Check configuration
python scripts/validate_config.py --client clientname

# Test connection
python scripts/test_connection.py --client clientname

# Test extraction (save HTML)
python scripts/test_extraction.py --client clientname --url "URL" --save

# Run test mode
python main.py --client clientname --test

# View real-time logs
tail -f {client}_scrapes/run_*/logs/scraper.log
```

### Resources

- **Documentation:** Review all docs in `docs/` directory
- **Examples:** Check `config/clients/agar/` for working example
- **Testing Scripts:** Use scripts in `scripts/` directory
- **Logs:** Always check log files first

---

## Prevention & Best Practices

### Prevent Issues Before They Happen

1. **Always validate configuration:**
   ```bash
   python scripts/validate_config.py --client clientname
   ```

2. **Test incrementally:**
   - Test connection first
   - Test extraction on sample URLs
   - Run test mode before full scrape

3. **Monitor first runs:**
   - Watch initial scrapes closely
   - Check logs regularly
   - Verify output quality

4. **Keep backups:**
   - Backup working configurations
   - Version control important files
   - Save successful scrape outputs

5. **Document changes:**
   - Note configuration changes
   - Record selector updates
   - Track what works and doesn't

---

**Still Need Help?**

If issues persist after following this guide:
- Review [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md)
- Check [configuration-guide.md](configuration-guide.md)
- Review [extraction-strategies.md](extraction-strategies.md)
- Contact 3DN support with diagnostic information

---

*3DN Scraper Template v1.0.0 - Professional Web Scraping Framework*
