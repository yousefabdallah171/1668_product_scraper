#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced WooCommerce Product Scraper for 1688.com
"""
import os
import sys
import csv
import time
import json
import random
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import cloudscraper
from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)

# User-Agent list for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

# Required WooCommerce CSV fields
WOOCOMMERCE_FIELDS = [
    'ID',
    'Type',
    'SKU',
    'Name',
    'Published',
    'Is featured?',
    'Visibility in catalog',
    'Short description',
    'Description',
    'Date sale price starts',
    'Date sale price ends',
    'Tax status',
    'Tax class',
    'In stock?',
    'Stock',
    'Backorders allowed?',
    'Sold individually?',
    'Weight (kg)',
    'Length (cm)',
    'Width (cm)',
    'Height (cm)',
    'Allow customer reviews?',
    'Purchase note',
    'Sale price',
    'Regular price',
    'Categories',
    'Tags',
    'Shipping class',
    'Images',
    'Download limit',
    'Download expiry days',
    'Parent',
    'Grouped products',
    'Upsells',
    'Cross-sells',
    'External URL',
    'Button text',
    'Position',
    'Attribute 1 name',
    'Attribute 1 value(s)',
    'Attribute 1 visible',
    'Attribute 1 global',
    'Attribute 2 name',
    'Attribute 2 value(s)',
    'Attribute 2 visible',
    'Attribute 2 global',
    'Meta: _wpcom_is_markdown',
    'Download 1 name',
    'Download 1 URL',
    'Download 2 name',
    'Download 2 URL'
]

class WooCommerceScraper:
    def __init__(self):
        self.session = self._create_session()
        self.output_dir = f"woocommerce_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.csv_file = os.path.join(self.output_dir, 'products.csv')
        self._init_csv()
        
    def _create_session(self):
        """Create a session with random user agent"""
        session = cloudscraper.create_scraper()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers'
        })
        return session
    
    def _init_csv(self):
        """Initialize CSV file with WooCommerce headers"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=WOOCOMMERCE_FIELDS)
            writer.writeheader()
    
    def _get_random_delay(self):
        """Get random delay between requests"""
        return random.uniform(2, 5)
    
    def _extract_product_data(self, soup, url):
        """Extract product data from the page"""
        try:
            # This is a simplified example - you'll need to adjust selectors based on 1688's HTML structure
            product = {field: '' for field in WOOCOMMERCE_FIELDS}
            
            # Basic product info
            product['Type'] = 'simple'
            product['SKU'] = f"1688-{url.split('/')[-1].split('.')[0]}"
            product['Name'] = soup.find('h1', {'class': 'title'}).get_text(strip=True)
            product['Published'] = '1'
            product['Visibility in catalog'] = 'visible'
            product['In stock?'] = '1'
            product['Allow customer reviews?'] = '1'
            
            # Price (example - adjust selector)
            price_elem = soup.find('span', {'class': 'price'})
            if price_elem:
                product['Regular price'] = price_elem.get_text(strip=True).replace('¥', '').strip()
            
            # Description (example - adjust selector)
            desc_elem = soup.find('div', {'class': 'description'})
            if desc_elem:
                product['Description'] = desc_elem.get_text(strip=True)
            
            # Images (example - adjust selector)
            images = []
            img_elems = soup.find_all('img', {'class': 'detail-gallery-img'})
            for i, img in enumerate(img_elems[:5]):  # Get first 5 images
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'http' in img_url:
                    images.append(img_url)
            product['Images'] = ', '.join(images)
            
            # Categories (you might want to set this based on your store structure)
            product['Categories'] = 'Imported Products'
            
            return product
            
        except Exception as e:
            logging.error(f"Error extracting product data: {str(e)}")
            return None
    
    def download_image(self, url, product_id, img_num):
        """Download and save product image"""
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Generate a unique filename
            ext = os.path.splitext(urlparse(url).path)[1] or '.jpg'
            filename = f"{product_id}_{img_num}{ext}"
            filepath = os.path.join(self.output_dir, 'images', filename)
            
            # Create images directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
                    
            return filepath
            
        except Exception as e:
            logging.error(f"Error downloading image {url}: {str(e)}")
            return None
    
    def process_url(self, url):
        """Process a single product URL"""
        try:
            logging.info(f"Processing URL: {url}")
            
            # Add delay between requests
            time.sleep(self._get_random_delay())
            
            # Fetch the page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we got a captcha or error page
            if 'captcha' in response.text.lower() or '验证' in response.text:
                logging.warning("Captcha detected. Please solve it manually and try again.")
                return None
            
            # Extract product data
            product = self._extract_product_data(soup, url)
            if not product:
                return None
            
            # Save product to CSV
            self._save_product_to_csv(product)
            
            return product
            
        except Exception as e:
            logging.error(f"Error processing URL {url}: {str(e)}")
            return None
    
    def _save_product_to_csv(self, product):
        """Save product data to CSV"""
        try:
            file_exists = os.path.isfile(self.csv_file)
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=WOOCOMMERCE_FIELDS)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(product)
                
            logging.info(f"Saved product to CSV: {product.get('Name', 'Unknown')}")
            
        except Exception as e:
            logging.error(f"Error saving product to CSV: {str(e)}")
    
    def run(self, urls):
        """Run the scraper for a list of URLs"""
        logging.info(f"Starting scraper for {len(urls)} URLs")
        
        success_count = 0
        failed_urls = []
        
        for i, url in enumerate(urls, 1):
            url = url.strip()
            if not url or url.startswith('#'):
                continue
                
            logging.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                result = self.process_url(url)
                if result:
                    success_count += 1
                else:
                    failed_urls.append(url)
            except Exception as e:
                logging.error(f"Unexpected error processing {url}: {str(e)}")
                failed_urls.append(url)
        
        # Save failed URLs for retry
        if failed_urls:
            with open(os.path.join(self.output_dir, 'failed_urls.txt'), 'w', encoding='utf-8') as f:
                f.write('\n'.join(failed_urls))
        
        # Generate summary
        summary = {
            'total_urls': len(urls),
            'successful': success_count,
            'failed': len(failed_urls),
            'output_directory': os.path.abspath(self.output_dir),
            'csv_file': os.path.abspath(self.csv_file),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(os.path.join(self.output_dir, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logging.info(f"\nScraping complete!")
        logging.info(f"Successfully processed: {success_count}/{len(urls)}")
        logging.info(f"Output directory: {os.path.abspath(self.output_dir)}")
        logging.info(f"CSV file: {os.path.abspath(self.csv_file)}")
        
        if failed_urls:
            logging.warning(f"Failed URLs saved to: {os.path.join(self.output_dir, 'failed_urls.txt')}")

def load_urls_from_file(filename):
    """Load URLs from a text file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

if __name__ == "__main__":
    print("=" * 80)
    print("ENHANCED WOOCOMMERCE PRODUCT SCRAPER FOR 1688.COM")
    print("=" * 80)
    
    # Check if URLs file exists
    urls_file = 'urls.txt'
    if not os.path.exists(urls_file):
        print(f"Error: {urls_file} not found in the current directory.")
        print("Please create a file named 'urls.txt' with one URL per line.")
        sys.exit(1)
    
    # Load URLs
    try:
        urls = load_urls_from_file(urls_file)
        if not urls:
            print("No valid URLs found in urls.txt")
            sys.exit(1)
            
        print(f"Loaded {len(urls)} URLs from {urls_file}")
        
        # Initialize and run scraper
        scraper = WooCommerceScraper()
        scraper.run(urls)
        
        print("\nScraping completed successfully!")
        print(f"Output directory: {os.path.abspath(scraper.output_dir)}")
        print(f"CSV file: {os.path.abspath(scraper.csv_file)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
