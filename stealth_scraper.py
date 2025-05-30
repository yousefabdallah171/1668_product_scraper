"""
Stealth Web Scraper with Anti-Detection Features
"""
import random
import time
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
import cloudscraper
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StealthScraper:
    """
    Advanced web scraper with anti-detection features including:
    - Rotating residential proxies
    - Randomized request delays
    - Dynamic headers rotation
    - Automatic retry and recovery
    - Browser fingerprinting protection
    """
    
    # Default user agents to rotate between
    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15',
    ]
    
    # Default accept languages
    ACCEPT_LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9,en-US;q=0.8',
        'en;q=0.9',
        'zh-CN,zh;q=0.9,en;q=0.8',
    ]
    
    def __init__(self, proxy_list: List[str] = None, max_retries: int = 3, 
                 request_timeout: int = 30, use_cloudscraper: bool = True):
        """
        Initialize the stealth scraper
        
        Args:
            proxy_list: List of proxy servers in format 'http://user:pass@ip:port' or 'socks5://user:pass@ip:port'
            max_retries: Maximum number of retries for failed requests
            request_timeout: Request timeout in seconds
            use_cloudscraper: Whether to use cloudscraper for bypassing anti-bot measures
        """
        self.proxy_list = proxy_list or []
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        self.use_cloudscraper = use_cloudscraper
        self.request_count = 0
        self.session = self._create_session()
        self.ua = UserAgent()
        
    def _create_session(self):
        """Create a new session with retry strategy"""
        if self.use_cloudscraper:
            return self._create_cloudscraper_session()
        return self._create_requests_session()
    
    def _create_requests_session(self):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Mount the retry strategy to all HTTP/HTTPS requests
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _create_cloudscraper_session(self):
        """Create a cloudscraper session with custom settings"""
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
            },
            delay=random.uniform(2, 7),  # Random delay between requests
            interpreter='nodejs',  # Use Node.js for better JS emulation
        )
        return scraper
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate random headers for each request"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.ua.random if hasattr(self, 'ua') else random.choice(self.DEFAULT_USER_AGENTS),
        }
        return headers
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the proxy list"""
        if not self.proxy_list:
            return None
            
        proxy = random.choice(self.proxy_list)
        return {
            'http': proxy,
            'https': proxy
        }
    
    def _throttle_requests(self):
        """Implement intelligent request throttling"""
        self.request_count += 1
        
        # Add random delay between requests (2-7 seconds)
        base_delay = random.uniform(2, 7)
        
        # Add additional delay every 50 requests
        if self.request_count % 50 == 0:
            base_delay += random.uniform(10, 30)
            logger.info(f"Adding additional delay after {self.request_count} requests")
        
        # Add some jitter
        jitter = random.choice([-0.5, -0.3, 0, 0.3, 0.5])
        delay = max(0.5, base_delay + jitter)  # Ensure minimum 0.5s delay
        
        logger.debug(f"Throttling: Waiting {delay:.2f}s before next request")
        time.sleep(delay)
    
    def _handle_error(self, response, url: str, attempt: int) -> Tuple[bool, str]:
        """Handle HTTP errors and determine if retry is needed"""
        if response is None:
            return True, "No response received"
            
        status_code = getattr(response, 'status_code', 0)
        
        if status_code == 200:
            return False, ""
            
        logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): "
                     f"Status {status_code} for {url}")
        
        if status_code in [429, 503]:
            retry_after = int(response.headers.get('Retry-After', random.randint(30, 120)))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry...")
            time.sleep(retry_after)
            return True, "Rate limited"
            
        if status_code >= 500:
            return attempt < self.max_retries - 1, f"Server error: {status_code}"
            
        if status_code in [403, 404]:
            return False, f"Access denied or page not found: {status_code}"
            
        return attempt < self.max_retries - 1, f"HTTP {status_code}"
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a GET request with anti-detection measures
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if all retries failed
        """
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a POST request with anti-detection measures
        
        Args:
            url: URL to post to
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if all retries failed
        """
        return self.request('POST', url, **kwargs)
    
    def request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make an HTTP request with anti-detection measures
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if all retries failed
        """
        # Set default timeout if not provided
        kwargs.setdefault('timeout', self.request_timeout)
        
        # Initialize response to handle the case where all retries fail
        response = None
        last_error = ""
        
        for attempt in range(self.max_retries):
            try:
                # Apply throttling between requests
                if attempt > 0 or self.request_count > 0:
                    self._throttle_requests()
                
                # Get fresh headers and proxy for each attempt
                headers = kwargs.pop('headers', {})
                headers.update(self._get_random_headers())
                kwargs['headers'] = headers
                
                # Set proxy if available
                if 'proxies' not in kwargs and self.proxy_list:
                    kwargs['proxies'] = self._get_random_proxy()
                
                # Make the request
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{self.max_retries})")
                
                if self.use_cloudscraper and isinstance(self.session, cloudscraper.CloudScraper):
                    # Use cloudscraper for the request
                    response = self.session.request(method, url, **kwargs)
                else:
                    # Use regular requests session
                    response = self.session.request(method, url, **kwargs)
                
                # Check for errors and determine if we should retry
                should_retry, error_msg = self._handle_error(response, url, attempt)
                if not should_retry:
                    if error_msg:
                        logger.error(f"Request failed: {error_msg}")
                    return response
                
                last_error = error_msg
                
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {last_error}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All {self.max_retries} attempts failed")
                    return None
                
                # Exponential backoff
                time.sleep(min(2 ** attempt, 60))  # Cap at 60 seconds
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts. Last error: {last_error}")
        return None
    
    def get_soup(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        """
        Get a BeautifulSoup object from a URL
        
        Args:
            url: URL to fetch and parse
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            BeautifulSoup object or None if request failed
        """
        response = self.get(url, **kwargs)
        if response is None:
            return None
            
        try:
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return None
    
    def download_file(self, url: str, save_path: str, chunk_size: int = 8192) -> bool:
        """
        Download a file with anti-detection measures
        
        Args:
            url: URL of the file to download
            save_path: Path to save the file
            chunk_size: Size of chunks to download at once
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Make the request
            response = self.get(url, stream=True)
            if response is None:
                return False
                
            # Save the file in chunks
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return False
