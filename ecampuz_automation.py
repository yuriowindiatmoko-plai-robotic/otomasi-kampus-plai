#!/usr/bin/env python3
"""
Selenium Automation Script for eCampuz Portal
Automates login, navigation, and PDF download from Pengelolaan Presensi
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pytesseract
from PIL import Image
import io

class EcampuzAutomation:
    def __init__(self, headless=False):
        """Initialize the automation with browser settings"""
        self.username = "2456769670130272"
        self.password = "SYEKH1"
        self.base_url = "https://start.plai.ecampuz.com/eakademikportal/"

        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # Force HTTP and prevent HTTPS redirects
        chrome_options.add_argument("--disable-features=HttpsUpgrades")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--aggressive-cache-discard")
        # Bypass HTTP security warnings
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://start.plai.ecampuz.com")

        # Download preferences
        prefs = {
            "download.default_directory": os.path.abspath("./downloads"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,  # Disable safe browsing to avoid HTTP warnings
            # Force HTTP settings
            "mixed_content_mode": 0,  # Allow mixed content
            "block_third_party_chips": False,
            "profile.default_content_setting_values": {
                "popups": 0,
                "notifications": 0,
                "geolocation": 0,
                "media_stream": 0,
                "insecure_content": 1,  # Allow insecure content
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Initialize driver using the same approach as tes.py
        try:
            from selenium.webdriver.chrome.service import Service
            service = Service("/usr/local/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("ChromeDriver initialized successfully")
        except Exception as e:
            print(f"ChromeDriver initialization failed: {e}")
            print("\nPlease install chromedriver manually by running:")
            print("sudo apt-get update")
            print("sudo apt-get install -y chromium-chromedriver")
            print("\nOr download it manually from: https://chromedriver.chromium.org/")
            raise Exception("ChromeDriver initialization failed. Please install chromedriver.")
        self.wait = WebDriverWait(self.driver, 10)

        # Create downloads directory
        os.makedirs("./downloads", exist_ok=True)

    def solve_captcha(self):
        """Extract and solve captcha from image"""
        try:
            # Find captcha image
            captcha_img = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='captcha']"))
            )

            # Get captcha image
            captcha_url = captcha_img.get_attribute('src')

            # Download captcha image
            response = requests.get(captcha_url)
            captcha_image = Image.open(io.BytesIO(response.content))

            # Convert to grayscale for better OCR
            captcha_image = captcha_image.convert('L')

            # Extract text using Tesseract
            captcha_text = pytesseract.image_to_string(captcha_image, config='--psm 8 --c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            captcha_text = captcha_text.strip().replace(" ", "")

            print(f"Detected captcha: {captcha_text}")
            return captcha_text

        except Exception as e:
            print(f"Error solving captcha: {e}")
            # Manual captcha fallback
            return input("Enter captcha manually: ")

    def close_ads_and_popups(self):
        """Close ads and popups very carefully to preserve login form"""
        print("Carefully closing ads and popups...")

        # First, check if login form already exists
        login_form_exists = False
        try:
            username_field = self.driver.find_element(By.NAME, "username")
            if username_field.is_displayed():
                login_form_exists = True
                print("Login form detected, being very careful with ad removal")
        except:
            pass

        # Only do aggressive ad removal if login form doesn't exist yet
        if not login_form_exists:
            # Try to find iframe with login form first
            self.find_login_iframe()

            # Very selective ad removal - avoid removing forms and inputs
            try:
                remove_script = """
                // Only remove elements that are clearly ads, not forms or inputs
                var adSelectors = [
                    '.adsbygoogle',
                    '.google-ads',
                    '.adsense',
                    '[class*="advertisement"]',
                    '[id*="advertisement"]',
                    '[class*="banner"]',
                    '[id*="banner"]'
                ];

                adSelectors.forEach(function(selector) {
                    var elements = document.querySelectorAll(selector);
                    elements.forEach(function(el) {
                        // Don't remove if it's in a form or contains form elements
                        var parentForm = el.closest('form');
                        var hasInputs = el.querySelector('input, button, select, textarea');

                        if (el && el.tagName.toLowerCase() !== 'form' && !parentForm && !hasInputs) {
                            el.style.display = 'none';
                        }
                    });
                });

                // Remove only ad-related scripts
                var scripts = document.querySelectorAll('script[src*="ads"], script[src*="googleads"], script[src*="doubleclick"]');
                scripts.forEach(function(script) {
                    if (script) {
                        script.remove();
                    }
                });
                """
                self.driver.execute_script(remove_script)
                print("Removed only obvious ads, preserving forms and inputs")
            except:
                pass

        # Try pressing Escape key once to close obvious popups
        try:
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE)
            actions.perform()
            print("Pressed ESC to close obvious popups")
            time.sleep(1)
        except:
            pass

        print("Finished careful ad removal")

    def find_login_iframe(self):
        """Find iframe containing login form"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")

            for i, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    time.sleep(0.5)  # Wait for iframe content

                    # Look for username field inside iframe
                    try:
                        username_in_frame = self.driver.find_element(By.NAME, "username")
                        if username_in_frame and username_in_frame.is_displayed():
                            print(f"Found login form in iframe {i}!")
                            self.found_login_in_iframe = True
                            self.login_iframe_index = i
                            print("Staying in iframe for login")
                            return True
                    except:
                        pass

                    # Also check for password field as fallback
                    try:
                        password_in_frame = self.driver.find_element(By.NAME, "password")
                        if password_in_frame and password_in_frame.is_displayed():
                            print(f"Found password field in iframe {i}!")
                            self.found_login_in_iframe = True
                            self.login_iframe_index = i
                            print("Staying in iframe for login")
                            return True
                    except:
                        pass

                    self.driver.switch_to.default_content()
                except:
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass

            print("No login form found in iframes")
            return False

        except:
            return False

    def debug_page_info(self):
        """Print debug information about current page"""
        try:
            print(f"\n--- PAGE DEBUG INFO ---")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page title: {self.driver.title}")

            # Count all forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"Forms found: {len(forms)}")

            # Count all input fields
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"Input fields found: {len(inputs)}")

            # Count iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Iframes found: {len(iframes)}")

            # Check first few input fields
            for i, inp in enumerate(inputs[:5]):
                try:
                    name = inp.get_attribute('name') or 'no-name'
                    inp_type = inp.get_attribute('type') or 'no-type'
                    displayed = inp.is_displayed()
                    print(f"  Input {i}: name='{name}', type='{inp_type}', visible={displayed}")
                except:
                    pass
            print("--- END DEBUG INFO ---\n")
        except:
            print("Could not gather debug info")

    def login(self):
        """Perform login to eCampuz portal"""
        print("Opening eCampuz portal...")
        self.driver.get(self.base_url)

        # Wait for page to load
        time.sleep(5)  # Increased wait time

        # Debug information
        self.debug_page_info()

        # Check if username field is immediately available before ad removal
        username_field = None
        try:
            username_field = self.driver.find_element(By.NAME, "username")
            if username_field.is_displayed():
                print("✓ Username field found immediately, no need for aggressive ad removal!")
        except:
            pass

        # Only do ad removal if username field not found
        if not username_field:
            print("Username field not immediately available, trying ad removal...")
            # Close ads/popups before accessing login form
            self.close_ads_and_popups()

            # Wait a bit more for any delayed popups
            time.sleep(3)
            self.close_ads_and_popups()

        # Try multiple times to find the username field with different strategies
        max_attempts = 3
        username_field = None

        for attempt in range(max_attempts):
            try:
                print(f"\n=== Attempt {attempt + 1} to find username field ===")
                print(f"Current context: {self.driver.current_url}")

                # Strategy 1: Check if we found login in iframe during ad cleanup
                if hasattr(self, 'found_login_in_iframe') and self.found_login_in_iframe:
                    print("Login form found in iframe, switching...")
                    try:
                        # Get iframes again and switch to the correct one
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        if hasattr(self, 'login_iframe_index') and self.login_iframe_index < len(iframes):
                            self.driver.switch_to.frame(iframes[self.login_iframe_index])
                            username_field = self.driver.find_element(By.NAME, "username")
                            print("Username field found in stored iframe!")
                        else:
                            # Fallback: check all iframes again
                            for i, iframe in enumerate(iframes):
                                try:
                                    self.driver.switch_to.frame(iframe)
                                    username_field = self.driver.find_element(By.NAME, "username")
                                    if username_field and username_field.is_displayed():
                                        print(f"Username field found in iframe {i}!")
                                        break
                                except:
                                    self.driver.switch_to.default_content()
                                    continue

                        if username_field:
                            print("✓ Username field found in iframe!")
                            break

                    except Exception as e:
                        print(f"Error accessing iframe: {e}")
                        self.driver.switch_to.default_content()

                # Strategy 2: Try main document first
                print("Checking main document for username field...")
                try:
                    username_field = self.driver.find_element(By.NAME, "username")
                    if username_field.is_displayed():
                        print("✓ Username field found in main document!")
                        break
                except:
                    pass

                # Strategy 3: Try different selectors
                selectors = [
                    "input[name='username']",
                    "input[name='user']",
                    "input[name='login']",
                    "input[id*='username']",
                    "input[id*='user']",
                    "input[type='text']",
                    "input[placeholder*='username']",
                    "input[placeholder*='user']"
                ]

                for selector in selectors:
                    try:
                        print(f"Trying selector: {selector}")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.get_attribute('name'):
                                print(f"Found element with name: {element.get_attribute('name')}")
                                username_field = element
                                break
                        if username_field:
                            break
                    except:
                        continue

                if username_field and username_field.is_displayed():
                    print("✓ Username field found with alternative selector!")
                    break

                # Strategy 4: Check all iframes more thoroughly
                print("Checking all iframes thoroughly...")
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                print(f"Found {len(iframes)} iframes to check")

                for i, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        time.sleep(1)  # Wait for iframe to load

                        # Check for username field with multiple selectors
                        for selector in selectors:
                            try:
                                username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if username_field and username_field.is_displayed():
                                    print(f"✓ Found username field in iframe {i} with selector {selector}")
                                    break
                            except:
                                continue

                        if username_field and username_field.is_displayed():
                            break

                        self.driver.switch_to.default_content()
                    except Exception as e:
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass

                if username_field and username_field.is_displayed():
                    print("✓ Username field found in iframe!")
                    break

                # If we get here, we didn't find the username field
                print("Username field not found with any method")

                # Debug: Print all input fields on page
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                print(f"Found {len(all_inputs)} input fields:")
                for i, inp in enumerate(all_inputs[:10]):  # Show first 10
                    try:
                        name = inp.get_attribute('name') or 'no-name'
                        inp_type = inp.get_attribute('type') or 'no-type'
                        placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                        displayed = inp.is_displayed()
                        print(f"  Input {i}: name='{name}', type='{inp_type}', placeholder='{placeholder}', displayed={displayed}")
                    except:
                        pass

                if attempt < max_attempts - 1:
                    print("Waiting and trying again...")
                    time.sleep(3)
                    self.close_ads_and_popups()

            except Exception as e:
                print(f"Error during attempt {attempt + 1}: {e}")
                if attempt == max_attempts - 1:
                    raise Exception(f"Could not find username field after {max_attempts} attempts")
                time.sleep(2)

        if not username_field or not username_field.is_displayed():
            raise Exception("Could not find a visible username field")

        # Handle readonly username field by removing readonly attribute
        try:
            # Remove readonly attribute using JavaScript first
            self.driver.execute_script("""
                var usernameField = document.querySelector('input[name="username"]');
                if (usernameField) {
                    usernameField.removeAttribute('readonly');
                    usernameField.focus();
                }
            """)
            print("Removed readonly attribute from username field")
        except:
            pass

        username_field.clear()
        username_field.send_keys(self.username)
        print("Username filled successfully")

        # Find and fill password field (handle iframe context)
        try:
            password_field = self.driver.find_element(By.NAME, "password")
        except:
            # If not found, might need to switch iframe contexts
            try:
                self.driver.switch_to.default_content()
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        self.driver.switch_to.frame(iframe)
                        password_field = self.driver.find_element(By.NAME, "password")
                        break
                    except:
                        self.driver.switch_to.default_content()
                        continue
            except:
                pass

        if password_field:
            password_field.clear()
            password_field.send_keys(self.password)
            print("Password filled successfully")
        else:
            raise Exception("Could not find password field")

        # Wait for captcha to render
        time.sleep(3)

        # Solve and input captcha (handle iframe context)
        captcha_text = self.solve_captcha()

        try:
            # Try to find captcha field in current context (iframe or main)
            captcha_field = self.driver.find_element(By.NAME, "captcha")
        except:
            # If not found and we're in iframe context, try switching contexts
            if hasattr(self, 'found_login_in_iframe') and self.found_login_in_iframe:
                try:
                    self.driver.switch_to.default_content()
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            self.driver.switch_to.frame(iframe)
                            captcha_field = self.driver.find_element(By.NAME, "captcha")
                            break
                        except:
                            self.driver.switch_to.default_content()
                            continue
                except:
                    pass

        if captcha_field:
            captcha_field.clear()
            captcha_field.send_keys(captcha_text)
            print("Captcha filled successfully")

            # Click login button (same context)
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                login_button.click()
                print("Login button clicked!")
            except:
                raise Exception("Could not find login button")
        else:
            raise Exception("Could not find captcha field")

        print("Login successful!")
        time.sleep(3)

    def navigate_to_presensi(self):
        """Navigate to Pengelolaan Presensi page"""
        print("Navigating to Pengelolaan Presensi...")

        # Click ACADEMICS tab
        academics_tab = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'ACADEMICS') or contains(text(), 'Academics')]"))
        )
        academics_tab.click()
        time.sleep(2)

        # Click Pengelolaan Presensi
        presensi_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Pengelolaan Presensi') or contains(text(), 'Presensi')]"))
        )
        presensi_link.click()
        time.sleep(3)

        print("Successfully navigated to Pengelolaan Presensi page")

    def download_presensi_pdf(self):
        """Download PDF from presensi page"""
        print("Downloading presensi PDF...")

        # Navigate to specific presensi URL
        presensi_url = "http://start.plai.ecampuz.com/eakademikportal/index.php?pModule=wtWoo6mboto=&pSub=08iflKeRpNiWqcqnpZ0=&pAct=0dWdoas=&kelas=k5NkY2diZJg=&smt=k5NmaGg="
        self.driver.get(presensi_url)
        time.sleep(3)

        try:
            # Click "Tampilkan" button if present
            tampilkan_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tampilkan') or contains(text(), 'Show')]"))
            )
            tampilkan_button.click()
            time.sleep(2)
        except:
            print("Tampilkan button not found, continuing...")

        try:
            # Find and click presensi link or download button
            presensi_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '.pdf')] | //button[contains(text(), 'Download')] | //a[contains(text(), 'PDF')]"))
            )

            # Get the PDF URL
            pdf_url = presensi_link.get_attribute('href')
            if pdf_url:
                # Download PDF using requests
                print(f"Downloading PDF from: {pdf_url}")
                response = requests.get(pdf_url)

                # Save PDF
                filename = f"./downloads/presensi_{int(time.time())}.pdf"
                with open(filename, 'wb') as f:
                    f.write(response.content)

                print(f"PDF saved as: {filename}")
                return filename
            else:
                # If it's a button, click it to trigger download
                presensi_link.click()
                time.sleep(5)
                print("PDF download initiated through browser")

        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None

    def extract_table_from_pdf(self, pdf_path):
        """Extract table data from downloaded PDF"""
        try:
            import tabula
            print(f"Extracting table from: {pdf_path}")

            # Extract tables from PDF
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)

            # Save tables to CSV
            for i, table in enumerate(tables):
                csv_filename = f"./downloads/table_{i+1}.csv"
                table.to_csv(csv_filename, index=False)
                print(f"Table {i+1} saved as: {csv_filename}")

            return tables

        except ImportError:
            print("tabula-py not installed. Install with: pip install tabula-py")
            return None
        except Exception as e:
            print(f"Error extracting table: {e}")
            return None

    def run_automation(self):
        """Run the complete automation process"""
        try:
            # Step 1: Login
            self.login()

            # Step 2: Navigate to presensi
            self.navigate_to_presensi()

            # Step 3: Download PDF
            pdf_path = self.download_presensi_pdf()

            # Step 4: Extract table from PDF (if available)
            if pdf_path:
                self.extract_table_from_pdf(pdf_path)

            print("Automation completed successfully!")

        except Exception as e:
            print(f"Automation failed: {e}")

        finally:
            # Keep browser open for inspection
            input("Press Enter to close browser...")
            self.driver.quit()

def main():
    """Main function to run the automation"""
    print("eCampuz Portal Automation")
    print("=" * 40)

    # Ask if user wants headless mode
    headless = input("Run in headless mode? (y/n): ").lower().startswith('y')

    # Create and run automation
    automation = EcampuzAutomation(headless=headless)
    automation.run_automation()

if __name__ == "__main__":
    main()