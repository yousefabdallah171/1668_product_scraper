"""
Utility functions for the 1688 scraper
"""
import os
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_file: str = 'scraper_config.json') -> Dict[str, Any]:
    """
    Load configuration from a JSON file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    default_config = {
        'scraper_settings': {
            'use_cloudscraper': True,
            'max_retries': 3,
            'request_timeout': 30,
            'min_delay': 2.0,
            'max_delay': 7.0,
            'batch_size': 50,
            'batch_delay': 30,
            'max_requests_per_hour': 1000,
            'user_agents': [],
            'accept_languages': ['en-US,en;q=0.9']
        },
        'proxy_settings': {
            'enabled': False,
            'proxy_list': [],
            'proxy_auth_required': False,
            'proxy_username': '',
            'proxy_password': '',
            'proxy_max_failures': 3,
            'proxy_health_check_url': 'https://www.google.com',
            'proxy_health_check_timeout': 10
        },
        'output_settings': {
            'output_dir': 'output',
            'log_file': 'scraper.log',
            'error_log_file': 'scraper_errors.log',
            'export_format': 'csv',
            'max_file_size_mb': 100,
            'max_files_to_keep': 10
        },
        'debug_settings': {
            'log_level': 'INFO',
            'save_html_on_error': True,
            'save_html_dir': 'debug_html',
            'print_debug_info': False
        }
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with default config to ensure all keys exist
                return _merge_dicts(default_config, config)
        else:
            # Create default config file if it doesn't exist
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            logger.warning(f"Created default config file: {config_file}")
            return default_config
    except Exception as e:
        logger.error(f"Error loading config file: {e}. Using default configuration.")
        return default_config

def _merge_dicts(default: Dict, custom: Dict) -> Dict:
    """Recursively merge two dictionaries"""
    result = default.copy()
    for key, value in custom.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def setup_logging(log_level: str = 'INFO', log_file: str = 'scraper.log'):
    """
    Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file
    """
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler
    try:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)) or '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.error(f"Failed to set up file logging: {e}")

def generate_session_id() -> str:
    """
    Generate a unique session ID
    
    Returns:
        str: A unique session ID
    """
    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices('abcdef0123456789', k=8))
    return f"sess_{timestamp}_{random_str}"

def get_timestamp() -> str:
    """
    Get current timestamp in a standard format
    
    Returns:
        str: Current timestamp in YYYYMMDD_HHMMSS format
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def create_output_dir(base_dir: str = 'output') -> str:
    """
    Create an output directory with timestamp
    
    Args:
        base_dir: Base directory name
        
    Returns:
        str: Path to the created directory
    """
    timestamp = get_timestamp()
    output_dir = os.path.join(base_dir, f'scrape_{timestamp}')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Input text
        
    Returns:
        str: Cleaned text
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Replace multiple whitespace with single space
    text = ' '.join(text.split())
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text.strip()

def format_price(price: Union[str, int, float]) -> str:
    """
    Format price string
    
    Args:
        price: Price value
        
    Returns:
        str: Formatted price string
    """
    if not price and price != 0:
        return ''
    
    try:
        # Handle string prices with currency symbols
        if isinstance(price, str):
            # Remove any non-numeric characters except decimal point
            price_str = ''.join(c for c in price if c.isdigit() or c in '.,')
            # Replace comma with dot if it's used as decimal separator
            if ',' in price_str and '.' in price_str:
                if price_str.find(',') < price_str.find('.'):
                    price_str = price_str.replace(',', '')
                else:
                    price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                # Check if comma is used as thousand separator or decimal point
                parts = price_str.split(',')
                if len(parts) > 1 and len(parts[-1]) == 2:
                    # Likely decimal point (e.g., 1,23)
                    price_str = price_str.replace(',', '.')
            
            price = float(price_str)
        
        # Format to 2 decimal places
        return f"{float(price):.2f}"
    except (ValueError, TypeError):
        return str(price)

def generate_product_hash(product_data: Dict[str, Any]) -> str:
    """
    Generate a unique hash for a product based on its data
    
    Args:
        product_data: Dictionary containing product data
        
    Returns:
        str: MD5 hash of the product data
    """
    # Create a string representation of the product data
    product_str = json.dumps(product_data, sort_keys=True)
    # Generate MD5 hash
    return hashlib.md5(product_str.encode('utf-8')).hexdigest()

def validate_url(url: str) -> bool:
    """
    Validate a URL
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL validation
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Check for valid domain characters
    domain = url.split('//', 1)[1].split('/', 1)[0]
    if not all(c.isalnum() or c in '.-' for c in domain):
        return False
    
    return True

def read_urls_from_file(file_path: str) -> List[str]:
    """
    Read URLs from a text file (one URL per line)
    
    Args:
        file_path: Path to the file containing URLs
        
    Returns:
        list: List of valid URLs
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    urls.append(line)
    except Exception as e:
        logger.error(f"Error reading URLs from file: {e}")
    
    # Filter and validate URLs
    valid_urls = [url for url in urls if validate_url(url)]
    
    if invalid_count := len(urls) - len(valid_urls):
        logger.warning(f"Skipped {invalid_count} invalid URLs")
    
    return valid_urls

def save_to_json(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        file_path: Path to the output file
        indent: Indentation level for pretty printing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)) or '.', exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving to JSON file {file_path}: {e}")
        return False

def load_from_json(file_path: str) -> Any:
    """
    Load data from a JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Any: Loaded data or None if failed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading from JSON file {file_path}: {e}")
        return None
