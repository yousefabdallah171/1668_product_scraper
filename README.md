# 🛍️ 1688.com Product Scraper for WooCommerce

A simple yet powerful tool to scrape product data from 1688.com and prepare it for WooCommerce import. This tool helps you quickly import products from 1688.com to your WooCommerce store with minimal effort.

![Scraper Demo](https://img.shields.io/badge/Status-Active-brightgreen) 
![Python](https://img.shields.io/badge/Python-3.8%2B-blue) 
![License](https://img.shields.io/badge/License-MIT-orange)

## ✨ Features

- Extract product details (name, description, price, images) from 1688.com
- Clean and format product data for WooCommerce
- Handle multiple product images
- Automatic translation of Chinese text to English
- Generate WooCommerce-compatible CSV files
- Simple and easy-to-use interface

## 🚀 Getting Started

### 📋 Prerequisites

1. **Windows 10 or later** (Mac/Linux users will need to adjust some steps)
2. **Google Chrome** web browser ([Download here](https://www.google.com/chrome/))
3. **Python 3.8 or higher** (We'll install this in the next steps)

## 🛠️ Installation Guide

### Step 1: Install Python

1. Download Python from the official website:
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Click on the yellow "Download Python" button
   - **IMPORTANT**: During installation, make sure to check the box that says "Add Python to PATH"
   - Click "Install Now" and wait for the installation to complete

2. Verify Python is installed:
   - Press `Windows + R` on your keyboard
   - Type `cmd` and press Enter
   - In the black window that appears, type: `python --version`
   - You should see a version number (like "Python 3.10.0"). If not, restart your computer and try again.

### Step 2: Download the Scraper

1. Click the green "Code" button at the top of this page
2. Click "Download ZIP"
3. Extract the ZIP file to a folder on your computer (right-click → Extract All...)
4. Remember where you extracted the files (like `C:\Users\YourName\Downloads\final_product_scraper-main`)

### Step 3: Install Required Programs

1. Open the Command Prompt (press `Windows + R`, type `cmd`, press Enter)
2. Type the following commands one by one, pressing Enter after each:
   ```
   pip install --upgrade pip
   pip install cloudscraper beautifulsoup4 requests pandas googletrans==3.1.0a0
   ```
3. Wait for the installations to complete (it might take a few minutes)

## 🚀 How to Use the Scraper

### Step 1: Prepare Your Product Links

1. Open Notepad (press `Windows + R`, type `notepad`, press Enter)
2. Paste your 1688.com product links, one per line
3. Save the file as `urls.txt` in the same folder as the scraper
   - In Notepad: File → Save As
   - Choose "All Files" as the file type
   - Name it `urls.txt`
   - Save it in the scraper folder

### Step 2: Run the Scraper

1. Open the scraper folder
2. Double-click on `run_scraper.bat`
   - If you don't see this file, right-click on `run_scraper.py` and select "Run with Python"
3. Wait for the script to finish (it might take a few minutes)
4. When it's done, you'll find a new file named like `woocommerce_import_YYYYMMDD_HHMMSS.csv`

### Step 3: Import to WooCommerce

1. Log in to your WordPress admin panel
2. Go to WooCommerce → Products → Import
3. Click "Choose File" and select the CSV file that was created
4. Click "Continue" and then "Run the importer"
5. Map the fields (the importer should do this automatically)
6. Click "Run the importer"

## ❓ Need Help?

If you encounter any issues:

1. Make sure you followed all the installation steps
2. Check that your internet connection is working
3. Try closing and reopening the Command Prompt
4. If you see any error messages, copy them and create an issue on GitHub

## 📝 Notes

- The scraper includes delays to avoid being blocked by 1688.com
- Some products might not have English descriptions - you may need to edit these manually
- For best results, don't scrape more than 20-30 products at once

## 🤝 Contributing

Feel free to submit issues and enhancement requests.

## 📄 License

This project is licensed under the MIT License.
   ```bash
   # Install core requirements
   pip install -r requirements.txt
   
   # For additional features (optional)
   pip install -r requirements.txt[all]
   ```

3. **Configuration**
   Copy the example configuration file and update it with your settings:
   ```bash
   cp config.example.json config.json
   ```

## ⚙️ Configuration

Edit `config.json` to customize the scraper's behavior:

```json
{
    "scraper": {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ],
        "request_delay": {
            "min": 2.0,
            "max": 7.0
        },
        "timeout": 30,
        "max_retries": 3,
        "concurrent_requests": 5
    },
    "proxy": {
        "enabled": false,
        "list": [
            "http://user:pass@proxy1:port",
            "socks5://user:pass@proxy2:port"
        ],
        "rotation_interval": 10,
        "health_check_url": "https://www.1688.com"
    },
    "output": {
        "directory": "data",
        "format": "json",
        "max_file_size_mb": 100,
        "save_images": true,
        "images_dir": "images"
    },
    "debug": {
        "level": "INFO",
        "save_failed_requests": true,
        "log_file": "scraper.log"
    }
}
```

## 🛠 Usage

### Basic Commands

```bash
# Scrape products from URLs file
python scraper.py scrape urls.txt -o products.json

# Check proxy health
python scraper.py check-proxies

# View help
python scraper.py --help
```

### Advanced Usage

```bash
# Scrape with custom config
python scraper.py scrape urls.txt -c config.json --format csv

# Limit number of concurrent requests
python scraper.py scrape urls.txt --concurrency 3

# Use specific proxy list
python scraper.py scrape urls.txt --proxies proxies.txt
```

## 📊 Output Format

The scraper outputs data in the following format:

```json
{
    "product_id": "123456789",
    "url": "https://detail.1688.com/offer/123456789.html",
    "title": "Product Name",
    "price": {
        "original": "¥99.00",
        "discounted": "¥79.00",
        "currency": "CNY"
    },
    "specifications": {
        "Color": "Black",
        "Size": "XL",
        "Material": "Cotton"
    },
    "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "description": "Detailed product description...",
    "seller_info": {
        "name": "Seller Name",
        "rating": 4.8,
        "response_rate": "98%"
    },
    "shipping": {
        "location": "Guangzhou, China",
        "free_shipping": true,
        "delivery_time": "7-15 days"
    },
    "scraped_at": "2025-05-26T14:30:45.123456Z"
}
```

## 🔒 Privacy and Legal

- This tool is for educational purposes only
- Respect website terms of service and robots.txt
- Use responsibly and consider website load
- The authors are not responsible for misuse

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please open an issue on GitHub.
