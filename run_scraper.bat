@echo off
echo 1688.com Product Scraper for WooCommerce
echo ================================
echo.
echo Making sure all required packages are installed...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org and make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Install required packages
echo.
echo Installing required Python packages...
python -m pip install --upgrade pip
pip install cloudscraper beautifulsoup4 requests pandas googletrans==3.1.0a0

:: Check if urls.txt exists
if not exist "urls.txt" (
    echo.
    echo ERROR: urls.txt file not found!
    echo Please create a file named 'urls.txt' in the same folder as this script.
    echo Add one 1688.com product URL per line in the file.
    echo.
    pause
    exit /b 1
)

:: Run the scraper
echo.
echo Starting the scraper...
python woocommerce_1688_scraper.py

:: Check if the script ran successfully
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Scraping completed successfully!
    echo Check the generated CSV file in this folder for your WooCommerce import.
) else (
    echo.
    echo An error occurred while running the scraper.
    echo Please check the error messages above for more information.
)

echo.
pause
