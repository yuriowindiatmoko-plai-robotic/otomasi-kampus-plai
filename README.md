# eCampuz Portal Automation

Selenium automation script for eCampuz academic portal login and PDF download from Pengelolaan Presensi.

## Features

- Automated login to eCampuz portal
- CAPTCHA solving using OCR (Tesseract)
- Navigation to ACADEMICS → Pengelolaan Presensi
- PDF download from presensi pages
- Table extraction from downloaded PDFs
- Headless mode support

## Prerequisites

1. **Python 3.7+** installed
2. **Tesseract OCR** installed on your system:
   - Ubuntu/Debian: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
3. **Google Chrome** browser

## Installation

1. Clone or download this project
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the automation script:
   ```bash
   python ecampuz_automation.py
   ```

2. Choose whether to run in headless mode (no visible browser):
   - Enter 'y' for headless mode
   - Enter 'n' to see the browser window

3. The script will:
   - Automatically log in with provided credentials
   - Navigate to Pengelolaan Presensi
   - Download the PDF file
   - Extract tables from the PDF (if tabula-py is available)

## Script Workflow

Based on your requirements, the script performs these steps:

1. **Login Process**
   - Opens: `https://start.plai.ecampuz.com/eakademikportal/`
   - Enters username: `2456769670130272`
   - Enters password: `SYEKH1`
   - Solves CAPTCHA using OCR
   - Clicks login button

2. **Navigation**
   - Clicks ACADEMICS tab
   - Clicks Pengelolaan Presensi
   - Navigates to presensi page with specific parameters

3. **PDF Download**
   - Downloads PDF from presensi page
   - Saves to `./downloads/` directory

4. **Table Extraction**
   - Extracts tables from downloaded PDF
   - Saves tables as CSV files

## Files Created

- `ecampuz_automation.py` - Main automation script
- `requirements.txt` - Python dependencies
- `downloads/` - Directory for downloaded PDFs and extracted tables

## Troubleshooting

### CAPTCHA Issues
If OCR fails to solve CAPTCHA:
1. The script will fall back to manual input
2. Enter the CAPTCHA manually when prompted
3. Consider adjusting Tesseract settings for better accuracy

### PDF Download Issues
If PDF download fails:
1. Check if the presensi page structure has changed
2. Verify the URL parameters are still valid
3. Ensure Chrome browser allows automatic downloads

### Table Extraction Issues
If table extraction fails:
1. Install Java (required by tabula-py)
2. Install tabula-py: `pip install tabula-py`
3. Check if PDF contains extractable tables

## Security Notes

- Credentials are hardcoded in the script for automation purposes
- Consider using environment variables for production use
- Ensure you have authorization to automate access to the portal

## Customization

To modify for different users or portals:
1. Update credentials in `__init__` method
2. Adjust URL patterns in navigation methods
3. Modify CAPTCHA solving approach if needed