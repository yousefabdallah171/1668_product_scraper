#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stealth Scraper CLI - Command-line interface for the stealth web scraper
"""
import os
import sys
import json
import time
import logging
import argparse
from typing import List, Dict, Optional, Any
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stealth_scraper import StealthScraper
from proxy_manager import ProxyManager
from scraper_utils import (
    load_config, setup_logging, generate_session_id, 
    get_timestamp, create_output_dir, clean_text, 
    format_price, generate_product_hash, validate_url, 
    read_urls_from_file, save_to_json, load_from_json
)

class StealthScraperCLI:
    """Command-line interface for the Stealth Scraper"""
    
    def __init__(self, config_file: str = 'scraper_config.json'):
        """
        Initialize the CLI
        
        Args:
            config_file: Path to the configuration file
        """
        self.config = load_config(config_file)
        self.session_id = generate_session_id()
        self.output_dir = create_output_dir(self.config['output_settings']['output_dir'])
        
        # Set up logging
        log_level = self.config['debug_settings']['log_level']
        log_file = os.path.join(self.output_dir, self.config['output_settings']['log_file'])
        setup_logging(log_level, log_file)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"Output directory: {self.output_dir}")
        
        # Initialize proxy manager if proxies are enabled
        self.proxy_manager = None
        if self.config['proxy_settings']['enabled'] and self.config['proxy_settings']['proxy_list']:
            self._init_proxy_manager()
        
        # Initialize the scraper
        self.scraper = self._init_scraper()
    
    def _init_proxy_manager(self) -> None:
        """Initialize the proxy manager"""
        proxy_settings = self.config['proxy_settings']
        
        self.proxy_manager = ProxyManager(
            proxy_list=proxy_settings['proxy_list'],
            max_failures=proxy_settings.get('proxy_max_failures', 3),
            health_check_url=proxy_settings.get('proxy_health_check_url', 'https://www.google.com'),
            health_check_timeout=proxy_settings.get('proxy_health_check_timeout', 10),
            auth_required=proxy_settings.get('proxy_auth_required', False),
            username=proxy_settings.get('proxy_username', ''),
            password=proxy_settings.get('proxy_password', '')
        )
        
        # Perform initial health check
        healthy, total = self.proxy_manager.health_check_all()
        self.logger.info(f"Proxy manager initialized. {healthy} of {total} proxies are healthy.")
    
    def _init_scraper(self) -> StealthScraper:
        """Initialize the stealth scraper"""
        scraper_settings = self.config['scraper_settings']
        
        # Get proxy for the scraper if proxy manager is available
        proxies = None
        if self.proxy_manager:
            proxy_config = self.proxy_manager.get_proxy(strategy='random')
            if proxy_config:
                proxies = proxy_config
        
        # Initialize the scraper
        scraper = StealthScraper(
            proxy_list=scraper_settings.get('proxy_list', []),
            max_retries=scraper_settings.get('max_retries', 3),
            request_timeout=scraper_settings.get('request_timeout', 30),
            use_cloudscraper=scraper_settings.get('use_cloudscraper', True)
        )
        
        return scraper
    
    def scrape_urls(self, urls: List[str], output_file: str = None) -> None:
        """
        Scrape a list of URLs
        
        Args:
            urls: List of URLs to scrape
            output_file: Optional output file path (default: auto-generated)
        """
        if not urls:
            self.logger.warning("No URLs provided to scrape")
            return
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs")
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = get_timestamp()
            output_file = os.path.join(self.output_dir, f'scraped_data_{timestamp}.json')
        
        results = []
        success_count = 0
        failure_count = 0
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Scraping URL {i}/{len(urls)}: {url}")
            
            try:
                # Get the page content
                response = self.scraper.get(url)
                
                if response is None:
                    self.logger.error(f"Failed to fetch URL: {url}")
                    failure_count += 1
                    continue
                
                # Parse the response
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract product information (customize this part based on your needs)
                product_info = {
                    'url': url,
                    'title': self._extract_title(soup),
                    'price': self._extract_price(soup),
                    'description': self._extract_description(soup),
                    'images': self._extract_images(soup, url),
                    'scraped_at': datetime.utcnow().isoformat(),
                    'session_id': self.session_id
                }
                
                # Add to results
                results.append(product_info)
                success_count += 1
                
                # Save progress periodically
                if i % 10 == 0 or i == len(urls):
                    self._save_results(results, output_file)
                
                # Log progress
                self.logger.info(f"Successfully scraped: {url}")
                
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
                failure_count += 1
                
                # Save debug HTML if enabled
                if self.config['debug_settings']['save_html_on_error']:
                    self._save_debug_html(url, response.text if 'response' in locals() else None, str(e))
        
        # Save final results
        self._save_results(results, output_file)
        
        # Print summary
        self.logger.info(f"Scraping completed. Success: {success_count}, Failed: {failure_count}")
        self.logger.info(f"Results saved to: {output_file}")
    
    def _extract_title(self, soup) -> str:
        """Extract product title from the page"""
        # Customize this method based on the target website structure
        title_elem = soup.find('h1')
        return clean_text(title_elem.get_text()) if title_elem else ""
    
    def _extract_price(self, soup) -> str:
        """Extract product price from the page"""
        # Customize this method based on the target website structure
        price_elem = soup.find(class_=lambda c: c and 'price' in c.lower())
        return format_price(price_elem.get_text()) if price_elem else ""
    
    def _extract_description(self, soup) -> str:
        """Extract product description from the page"""
        # Customize this method based on the target website structure
        desc_elem = soup.find('div', class_=lambda c: c and 'description' in c.lower())
        return clean_text(desc_elem.get_text()) if desc_elem else ""
    
    def _extract_images(self, soup, base_url: str) -> List[str]:
        """Extract product images from the page"""
        # Customize this method based on the target website structure
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith(('http://', 'https://')):
                images.append(src)
            else:
                # Convert relative URLs to absolute
                images.append(requests.compat.urljoin(base_url, src))
        return images
    
    def _save_results(self, results: List[Dict], output_file: str) -> None:
        """Save scraping results to a file"""
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)) or '.', exist_ok=True)
            
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Saved {len(results)} results to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}", exc_info=True)
    
    def _save_debug_html(self, url: str, content: str, error: str) -> None:
        """Save debug HTML for failed requests"""
        try:
            debug_dir = os.path.join(self.output_dir, 'debug_html')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Create a safe filename from the URL
            safe_url = "".join(c for c in url if c.isalnum() or c in '.-_')
            safe_url = safe_url[:100]  # Limit filename length
            
            timestamp = get_timestamp()
            filename = f"error_{timestamp}_{safe_url}.html"
            filepath = os.path.join(debug_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"<!-- URL: {url} -->\n")
                f.write(f"<!-- Error: {error} -->\n\n")
                if content:
                    f.write(content)
            
            self.logger.debug(f"Saved debug HTML to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving debug HTML: {str(e)}", exc_info=True)
    
    def run(self) -> None:
        """Run the CLI"""
        parser = argparse.ArgumentParser(description='Stealth Web Scraper')
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # Scrape command
        scrape_parser = subparsers.add_parser('scrape', help='Scrape URLs from a file')
        scrape_parser.add_argument('input_file', help='File containing URLs (one per line)')
        scrape_parser.add_argument('-o', '--output', help='Output file path')
        
        # Check proxies command
        proxy_parser = subparsers.add_parser('check-proxies', help='Check proxy health')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == 'scrape':
                urls = read_urls_from_file(args.input_file)
                if not urls:
                    self.logger.error("No valid URLs found in the input file")
                    return
                
                self.scrape_urls(urls, args.output)
                
            elif args.command == 'check-proxies':
                if not self.proxy_manager:
                    self.logger.warning("Proxy support is not enabled in the configuration")
                    return
                
                healthy, total = self.proxy_manager.health_check_all()
                self.logger.info(f"Proxy health check: {healthy} of {total} proxies are healthy")
                
                # Print detailed stats
                stats = self.proxy_manager.get_stats()
                for proxy, stat in stats.items():
                    self.logger.info(f"\nProxy: {proxy}")
                    for k, v in stat.items():
                        self.logger.info(f"  {k}: {v}")
            
            else:
                parser.print_help()
        
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}", exc_info=True)


def main():
    """Main entry point"""
    try:
        cli = StealthScraperCLI()
        cli.run()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
