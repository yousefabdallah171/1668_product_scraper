#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified 1688.com Product Scraper with system check bypass
"""
import os
import sys
import woocommerce_1688_scraper as scraper

def main():
    """Main function that bypasses system checks"""
    print("\n" + "=" * 80)
    print("MODIFIED 1688 SCRAPER FOR WOOCOMMERCE")
    print("Bypassing system checks...")
    print("=" * 80)
    
    # Check for URLs file
    if not os.path.exists('urls.txt'):
        print("\n❌ Error: urls.txt not found")
        print("Please create urls.txt with one URL per line")
        sys.exit(1)
    
    # Start main process - cleanup is handled within the run() function
    scraper.run()

if __name__ == "__main__":
    main()
