"""
Proxy Manager for handling proxy rotation and health checks
"""
import random
import time
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

@dataclass
class ProxyStats:
    """Track statistics for a proxy"""
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0
    last_used: float = 0.0
    last_failure: float = 0.0
    consecutive_failures: int = 0
    is_active: bool = True

class ProxyManager:
    """
    Manages a pool of proxies with health checking and rotation
    """
    
    def __init__(self, 
                 proxy_list: List[str] = None,
                 max_failures: int = 3,
                 health_check_url: str = 'https://www.google.com',
                 health_check_timeout: int = 10,
                 health_check_interval: int = 300,
                 auth_required: bool = False,
                 username: str = None,
                 password: str = None):
        """
        Initialize the ProxyManager
        
        Args:
            proxy_list: List of proxy URLs in format 'http://user:pass@host:port' or 'socks5://host:port'
            max_failures: Maximum number of consecutive failures before marking a proxy as inactive
            health_check_url: URL to use for health checks
            health_check_timeout: Timeout for health check requests in seconds
            health_check_interval: Minimum time between health checks for a single proxy in seconds
            auth_required: Whether authentication is required for the proxies
            username: Username for proxy authentication
            password: Password for proxy authentication
        """
        self.proxies = proxy_list or []
        self.max_failures = max_failures
        self.health_check_url = health_check_url
        self.health_check_timeout = health_check_timeout
        self.health_check_interval = health_check_interval
        self.auth_required = auth_required
        self.username = username
        self.password = password
        
        # Track proxy statistics
        self.proxy_stats: Dict[str, ProxyStats] = {}
        self.active_proxies: Set[str] = set()
        self.banned_proxies: Set[str] = set()
        
        # Initialize stats for all proxies
        for proxy in self.proxies:
            self.proxy_stats[proxy] = ProxyStats()
            self.active_proxies.add(proxy)
        
        # Create a session for health checks
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        # Mount the retry strategy to all HTTP/HTTPS requests
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_proxy(self, strategy: str = 'random') -> Optional[Dict[str, str]]:
        """
        Get a proxy from the pool based on the specified strategy
        
        Args:
            strategy: Strategy to use for proxy selection ('random', 'round_robin', 'fastest')
            
        Returns:
            dict: Proxy configuration in the format {'http': 'proxy_url', 'https': 'proxy_url'}
                  or None if no active proxies are available
        """
        if not self.active_proxies:
            logger.warning("No active proxies available")
            return None
        
        # Filter out proxies that need health checking
        current_time = time.time()
        available_proxies = []
        
        for proxy in self.active_proxies:
            stats = self.proxy_stats[proxy]
            # Skip proxies that are due for a health check
            if current_time - stats.last_used > self.health_check_interval:
                self._check_proxy_health(proxy)
            
            if stats.is_active:
                available_proxies.append(proxy)
        
        if not available_proxies:
            logger.warning("No healthy proxies available")
            return None
        
        # Select proxy based on strategy
        if strategy == 'random':
            selected_proxy = random.choice(available_proxies)
        elif strategy == 'round_robin':
            # Sort by last used time (oldest first)
            sorted_proxies = sorted(
                available_proxies,
                key=lambda p: self.proxy_stats[p].last_used
            )
            selected_proxy = sorted_proxies[0]
        elif strategy == 'fastest':
            # Sort by average response time (fastest first)
            sorted_proxies = sorted(
                available_proxies,
                key=lambda p: (
                    self.proxy_stats[p].total_response_time / 
                    max(1, self.proxy_stats[p].success_count)
                )
            )
            selected_proxy = sorted_proxies[0]
        else:
            logger.warning(f"Unknown proxy selection strategy: {strategy}. Using 'random'.")
            selected_proxy = random.choice(available_proxies)
        
        # Update last used time
        self.proxy_stats[selected_proxy].last_used = current_time
        
        # Format the proxy for requests
        return self._format_proxy(selected_proxy)
    
    def _format_proxy(self, proxy_url: str) -> Dict[str, str]:
        """
        Format proxy URL for use with requests
        
        Args:
            proxy_url: Proxy URL in format 'protocol://[user:pass@]host:port'
            
        Returns:
            dict: Proxy configuration for requests
        """
        if self.auth_required and self.username and self.password:
            # Extract protocol and host:port
            protocol = proxy_url.split('://')[0]
            host_port = proxy_url.split('://')[1] if '://' in proxy_url else proxy_url
            
            # Rebuild with authentication
            proxy_with_auth = f"{protocol}://{self.username}:{self.password}@{host_port}"
            return {
                'http': proxy_with_auth,
                'https': proxy_with_auth
            }
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def report_success(self, proxy_url: str, response_time: float):
        """
        Report a successful request through a proxy
        
        Args:
            proxy_url: The proxy URL that was used
            response_time: The response time in seconds
        """
        if proxy_url not in self.proxy_stats:
            return
        
        stats = self.proxy_stats[proxy_url]
        stats.success_count += 1
        stats.total_response_time += response_time
        stats.consecutive_failures = 0
        stats.is_active = True
        stats.last_used = time.time()
        
        # If this proxy was banned, reactivate it
        if proxy_url in self.banned_proxies:
            self.banned_proxies.remove(proxy_url)
            self.active_proxies.add(proxy_url)
            logger.info(f"Reactivated previously banned proxy: {proxy_url}")
    
    def report_failure(self, proxy_url: str, error: str = None):
        """
        Report a failed request through a proxy
        
        Args:
            proxy_url: The proxy URL that was used
            error: Optional error message
        """
        if proxy_url not in self.proxy_stats:
            return
        
        stats = self.proxy_stats[proxy_url]
        stats.failure_count += 1
        stats.consecutive_failures += 1
        stats.last_failure = time.time()
        
        if error:
            logger.warning(f"Proxy {proxy_url} failed with error: {error}")
        
        # Check if we should ban this proxy
        if stats.consecutive_failures >= self.max_failures:
            stats.is_active = False
            if proxy_url in self.active_proxies:
                self.active_proxies.remove(proxy_url)
            self.banned_proxies.add(proxy_url)
            logger.warning(f"Banned proxy {proxy_url} after {stats.consecutive_failures} consecutive failures")
    
    def _check_proxy_health(self, proxy_url: str) -> bool:
        """
        Check if a proxy is healthy
        
        Args:
            proxy_url: The proxy URL to check
            
        Returns:
            bool: True if the proxy is healthy, False otherwise
        """
        if proxy_url not in self.proxy_stats:
            return False
        
        stats = self.proxy_stats[proxy_url]
        current_time = time.time()
        
        # Don't check too frequently
        if current_time - stats.last_used < self.health_check_interval:
            return stats.is_active
        
        logger.debug(f"Checking health of proxy: {proxy_url}")
        
        proxies = self._format_proxy(proxy_url)
        start_time = time.time()
        
        try:
            response = self.session.get(
                self.health_check_url,
                proxies=proxies,
                timeout=self.health_check_timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.report_success(proxy_url, response_time)
                return True
            else:
                self.report_failure(proxy_url, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.report_failure(proxy_url, str(e))
            return False
    
    def health_check_all(self) -> Tuple[int, int]:
        """
        Check the health of all proxies
        
        Returns:
            tuple: (number_of_healthy_proxies, total_number_of_proxies)
        """
        healthy_count = 0
        
        for proxy in list(self.proxy_stats.keys()):
            if self._check_proxy_health(proxy):
                healthy_count += 1
        
        return healthy_count, len(self.proxy_stats)
    
    def add_proxy(self, proxy_url: str) -> bool:
        """
        Add a new proxy to the pool
        
        Args:
            proxy_url: Proxy URL to add
            
        Returns:
            bool: True if the proxy was added, False if it already exists
        """
        if not proxy_url or not isinstance(proxy_url, str):
            return False
            
        # Normalize the proxy URL
        proxy_url = proxy_url.strip()
        
        if not proxy_url:
            return False
            
        # Add protocol if missing
        if not proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy_url = f'http://{proxy_url}'
        
        # Check if proxy already exists
        if proxy_url in self.proxy_stats:
            return False
        
        # Add the proxy
        self.proxies.append(proxy_url)
        self.proxy_stats[proxy_url] = ProxyStats()
        self.active_proxies.add(proxy_url)
        
        # Perform initial health check
        self._check_proxy_health(proxy_url)
        
        return True
    
    def remove_proxy(self, proxy_url: str) -> bool:
        """
        Remove a proxy from the pool
        
        Args:
            proxy_url: Proxy URL to remove
            
        Returns:
            bool: True if the proxy was removed, False if it didn't exist
        """
        if proxy_url in self.proxy_stats:
            del self.proxy_stats[proxy_url]
            
            if proxy_url in self.proxies:
                self.proxies.remove(proxy_url)
                
            if proxy_url in self.active_proxies:
                self.active_proxies.remove(proxy_url)
                
            if proxy_url in self.banned_proxies:
                self.banned_proxies.remove(proxy_url)
                
            return True
            
        return False
    
    def get_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all proxies
        
        Returns:
            dict: Dictionary mapping proxy URLs to their statistics
        """
        return {
            proxy: {
                'success_count': stats.success_count,
                'failure_count': stats.failure_count,
                'avg_response_time': (
                    stats.total_response_time / max(1, stats.success_count)
                    if stats.success_count > 0 else 0
                ),
                'last_used': time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(stats.last_used)
                ) if stats.last_used > 0 else 'Never',
                'last_failure': time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(stats.last_failure)
                ) if stats.last_failure > 0 else 'Never',
                'consecutive_failures': stats.consecutive_failures,
                'is_active': stats.is_active
            }
            for proxy, stats in self.proxy_stats.items()
        }
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
