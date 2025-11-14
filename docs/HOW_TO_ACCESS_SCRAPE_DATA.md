# How to Access Scrape Data

## Current Running Job

**Job ID**: `ad355838-0c0c-4477-ab96-86cb4e1f8672`
**Folder**: `20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672`
**Status**: RUNNING ⏳

## 📍 Data Location

### Inside Docker Container

```bash
./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

### On Your Mac (Host Machine)

The data is stored in a Docker volume that maps to:

```bash
/Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

## 📊 Current Statistics

- **JSON Files**: 69+ (growing)
- **Directories**: 9
- **Main Structure**: `categories/` folder with subcategories

## 🔍 Ways to Access the Data

### Method 1: Direct File Access on Mac

**Easiest method** - Just browse the files on your Mac:

```bash
# Navigate to the folder
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/

# List all files
ls -lh

# View categories
ls -lh categories/

# Read a file
cat categories/all-purpose-floor-cleaners_products.json | jq
```

### Method 2: Through Docker Container

```bash
# List files
docker-compose exec api ls -la ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/

# View a file
docker-compose exec api cat ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/categories/all-purpose-floor-cleaners_products.json

# Copy file to local directory
docker cp scraper-api:/app/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ ./local_copy/
```

### Method 3: Via API

```bash
# Get job results via API
TOKEN="your_token_here"
curl -s http://localhost:3010/api/scraper/jobs/ad355838-0c0c-4477-ab96-86cb4e1f8672/results \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Method 4: Using Finder (GUI)

1. Open Finder
2. Press `Cmd + Shift + G` (Go to Folder)
3. Enter: `/Users/mick/AI/c4ai/agar/scraper_data/jobs/`
4. Look for folder: `20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672`
5. Double-click to browse

## 📁 Folder Structure

```
20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
└── categories/
    ├── air-fresheners/
    │   ├── air-fresheners.json                           (category info)
    │   ├── air-fresheners_products.json                  (product list)
    │   └── detergent-deodorisers/
    │       └── detergent-deodorisers_products.json
    │
    ├── all-purpose-floor-cleaners.json
    ├── all-purpose-floor-cleaners_products.json
    │
    ├── carpet-cleaners/
    │   ├── carpet-cleaners.json
    │   ├── carpet-cleaners_products.json
    │   ├── carpet-cleaners-treatments/
    │   ├── restoration/
    │   ├── carpet-spotters-and-stain-removers/
    │   └── pre-spraying-hot-water-extraction-formulations/
    │
    ├── floor-care/
    ├── kitchen-care/
    ├── laundry-products/
    └── ... (more categories)
```

## 📝 File Types

### Category Info Files
- **Name Pattern**: `{category-name}.json`
- **Content**: Category metadata, URL, subcategories
- **Example**: `air-fresheners.json`

### Product List Files
- **Name Pattern**: `{category-name}_products.json`
- **Content**: Array of product URLs and basic info
- **Example**: `air-fresheners_products.json`

## 🔎 Exploring the Data

### List All Category Files

```bash
# On Mac
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
find . -name "*_products.json"

# Via Docker
docker-compose exec api find ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ -name "*_products.json"
```

### Count Products Collected

```bash
# On Mac
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
find . -name "*_products.json" -exec cat {} \; | jq -s 'map(.[]) | length'

# Via Docker
docker-compose exec api sh -c 'find ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ -name "*_products.json" -exec cat {} \;' | jq -s 'map(.[]) | length'
```

### View a Specific File

```bash
# On Mac (with jq for pretty formatting)
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
cat categories/all-purpose-floor-cleaners_products.json | jq

# Via Docker
docker-compose exec api cat ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/categories/all-purpose-floor-cleaners_products.json | jq
```

### Search for Specific Products

```bash
# On Mac
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
grep -r "PRODUCT_NAME" categories/

# Via Docker
docker-compose exec api grep -r "PRODUCT_NAME" ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/categories/
```

## 📥 Export/Download Data

### Copy Entire Folder to Desktop

```bash
# On Mac
cp -r /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ ~/Desktop/agar_scrape_data/

# Via Docker
docker cp scraper-api:/app/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ ~/Desktop/agar_scrape_data/
```

### Create Archive (ZIP)

```bash
# On Mac
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/
zip -r agar_scrape_20251113_234931.zip 20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/

# Move to Desktop
mv agar_scrape_20251113_234931.zip ~/Desktop/
```

### Export to CSV (if needed)

```bash
# Convert JSON to CSV (using jq)
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/

# Example: Export product URLs
find categories -name "*_products.json" -exec cat {} \; | \
  jq -r '.[] | [.url, .name, .category] | @csv' > ~/Desktop/agar_products.csv
```

## 🔄 Monitor Real-Time Updates

### Watch Files Being Created

```bash
# On Mac
watch -n 5 'ls -lh /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/categories/ | wc -l'

# Or manually
ls -lh /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/categories/
```

### Check Folder Size

```bash
# On Mac
du -sh /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/

# Via Docker
docker-compose exec api du -sh ./scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

## 🎯 Quick Access Commands

### Open in Finder (Mac)

```bash
open /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

### Open in VS Code

```bash
code /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

### Open in Terminal

```bash
cd /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/
```

## 📋 Sample Data Structure

### Category File (`categories/air-fresheners.json`)
```json
{
  "name": "Air Fresheners & Deodorisers",
  "url": "https://agar.com.au/product-category/air-fresheners/",
  "subcategories": [
    {
      "name": "Detergent Deodorisers",
      "url": "https://agar.com.au/product-category/air-fresheners/detergent-deodorisers/"
    }
  ]
}
```

### Product List File (`categories/air-fresheners_products.json`)
```json
[
  {
    "url": "https://agar.com.au/product/product-name/",
    "name": "Product Name",
    "category": "Air Fresheners & Deodorisers",
    "image": "https://agar.com.au/wp-content/uploads/image.jpg"
  }
]
```

## 🚨 Important Notes

1. **Data is Growing**: The scraper is still running, so files are being added continuously
2. **No Product Details Yet**: Current files contain product URLs and basic info. Detailed scraping happens next
3. **Categories First**: The scraper collects all categories and product URLs before scraping details
4. **Final Output**: When complete, there will be an `all_products.json` file with all collected data

## 🔄 When Scrape Completes

Once the job completes, you'll see additional files:
- `all_products.json` - All product data combined
- `products/` - Individual product detail files
- `screenshots/` - Product screenshots (if enabled)
- `pdfs/` - PDF downloads (SDS, PDS files)
- `results.json` - Summary results

## 💡 Pro Tips

### Use jq for JSON Parsing

```bash
# Pretty print
cat file.json | jq

# Extract specific field
cat file.json | jq '.[].url'

# Filter results
cat file.json | jq '.[] | select(.category == "Air Fresheners")'

# Count items
cat file.json | jq 'length'
```

### Use grep for Searching

```bash
# Search all files
grep -r "search term" categories/

# Case-insensitive search
grep -ri "search term" categories/

# Show filename and line number
grep -rn "search term" categories/
```

### Monitor Progress

```bash
# Count JSON files
find /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ -name "*.json" | wc -l

# Watch file count grow
watch -n 10 'find /Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/ -name "*.json" | wc -l'
```

## 📞 Need Help?

If you need to:
- **Access specific data**: Use the file paths above
- **Export data**: Use the copy/zip commands
- **Parse JSON**: Use `jq` or open in VS Code
- **View in browser**: Copy files to a web-accessible location

The data is all stored locally on your Mac at:
**`/Users/mick/AI/c4ai/agar/scraper_data/jobs/20251113_234931_ad355838-0c0c-4477-ab96-86cb4e1f8672/`**
