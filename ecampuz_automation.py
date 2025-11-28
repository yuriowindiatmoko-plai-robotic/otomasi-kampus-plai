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
        """Extract and solve captcha from image with multiple methods"""
        print("Attempting to solve captcha...")

        try:
            # Wait for captcha to be rendered (JavaScript-based captchas need time)
            print("Waiting for captcha to render...")
            time.sleep(3)

            # Try different captcha selectors including non-image elements
            captcha_selectors = [
                # Image-based selectors (most specific first)
                "img[src*='captcha'][id*='captcha']",
                "img[alt*='captcha'][id*='captcha']",
                "img[src*='Captcha'][id*='captcha']",
                "img[alt*='Captcha'][id*='captcha']",
                "img.captcha",
                "#captcha img",
                ".captcha img",
                "img[src*='captcha']",
                "img[src*='Captcha']",
                "img[alt*='captcha']",
                "img[alt*='Captcha']",
                "img[src*='code']",
                "img[src*='verify']",

                # Canvas-based captchas
                "canvas[id*='captcha']",
                "canvas[class*='captcha']",
                "#captchaCanvas",
                ".captchaCanvas",

                # More specific div-based captchas (exclude progress bars)
                ".captcha-image",
                "#captcha-image",
                "div[id*='captchaImage']",
                "div[class*='captchaImage']",
                "div[id*='captchaImg']",
                "div[class*='captchaImg']",
                "div[id*='captcha-display']",
                "div[class*='captcha-display']",
                "div[id*='captcha-area']",
                "div[class*='captcha-area']",
                "div[id*='captcha-container']",
                "div[class*='captcha-container']",
                "[data-captcha-image]",
                "[style*='captcha'][style*='image']",
                "[style*='background-image'][style*='captcha']",

                # Input-based captcha fields
                "input[name='captcha_answer']",
                "input[name*='captcha']",
                "input[name*='code']",
                "input[name*='verify']",

                # General captcha elements (but exclude progress bars)
                ".captcha:not(.progress):not(.progress-bar)",
                "#captcha:not(.progress):not(.progress-bar)",
                "div[id*='captcha']:not(.progress):not(.progress-bar):not([class*='progress'])",
                "div[class*='captcha']:not(.progress):not(.progress-bar):not([class*='progress'])",

                # SVG captchas
                "svg[id*='captcha']",
                "svg[class*='captcha']",

                # Generic fallbacks (but exclude progress/loading)
                "img[src*='securi']",
                "img[src*='random']",
                "img[src*='image']",
                "[data-captcha]:not(.progress)",
                "[onclick*='captcha']:not(.progress)"
            ]

            captcha_img = None
            captcha_type = None

            for selector in captcha_selectors:
                try:
                    # Find all elements matching the selector (there might be multiple)
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if not element or not element.is_displayed():
                            continue

                        # Skip progress bars and loading elements
                        element_classes = element.get_attribute('class') or ''
                        element_id = element.get_attribute('id') or ''
                        element_text = element.text.strip()

                        if (any(progress_class in element_classes.lower() for progress_class in ['progress', 'loading', 'spinner', 'bar']) or
                            any(progress_id in element_id.lower() for progress_id in ['progress', 'loading', 'spinner', 'bar']) or
                            'progress-bar' in element_classes or
                            'progress' in element_id):
                            print(f"Skipping progress/loading element: {selector} (id: {element_id}, class: {element_classes})")
                            continue

                        # Skip elements with no content or very small elements (likely icons)
                        if (element.tag_name.lower() == 'div' and
                            not element_text and
                            not element.get_attribute('style') or
                            'background-image' not in (element.get_attribute('style') or '')):
                            # For divs, check if they have background image or actual content
                            style = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).backgroundImage;", element
                            )
                            if not style or style == 'none':
                                print(f"Skipping div with no background image: {selector}")
                                continue

                        print(f"Found captcha with selector: {selector}")
                        print(f"  Element ID: {element_id}")
                        print(f"  Element classes: {element_classes}")
                        print(f"  Element text: '{element_text}'")

                        # Determine captcha type
                        tag_name = element.tag_name.lower()
                        if tag_name == 'canvas':
                            captcha_type = 'canvas'
                        elif tag_name == 'svg':
                            captcha_type = 'svg'
                        elif tag_name == 'img':
                            captcha_type = 'image'
                        elif tag_name == 'input':
                            captcha_type = 'input'
                        else:
                            captcha_type = 'div'

                        captcha_img = element
                        print(f"Captcha type detected: {captcha_type}")
                        break
                    if captcha_img:
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue

            if not captcha_img:
                # Try to find any element that might contain captcha text or question
                print("No image/captcha found, looking for text-based captcha...")
                captcha_text_element = self._find_text_captcha()
                if captcha_text_element:
                    print("Found text-based captcha!")
                    return self._solve_text_captcha(captcha_text_element)

                # Comprehensive debugging - check all elements
                print("Comprehensive page analysis for potential captcha elements...")
                self._comprehensive_captcha_analysis()

                raise Exception("Captcha element not found with any selector")

            # Handle different captcha types
            if captcha_type == 'canvas':
                captcha_text = self._solve_canvas_captcha(captcha_img)
            elif captcha_type == 'svg':
                captcha_text = self._solve_svg_captcha(captcha_img)
            elif captcha_type == 'image':
                captcha_text = self._solve_image_captcha(captcha_img)
            else:  # div or other element
                captcha_text = self._solve_div_captcha(captcha_img)

            if captcha_text and len(captcha_text) >= 3:  # Valid captcha found
                print(f"✓ Successfully solved captcha: '{captcha_text}'")
                return captcha_text
            else:
                raise Exception("All captcha solving methods failed")

        except Exception as e:
            print(f"⚠ Captcha solving failed: {e}")
            return self._manual_captcha_fallback()

    def _solve_image_captcha(self, captcha_img):
        """Solve traditional image-based captcha"""
        print("Solving image-based captcha...")

        # Get captcha image URL and download
        captcha_url = captcha_img.get_attribute('src')
        print(f"Captcha URL: {captcha_url}")

        # Handle relative URLs
        if captcha_url and captcha_url.startswith('/'):
            captcha_url = self.base_url.rstrip('/') + captcha_url
        elif captcha_url and not captcha_url.startswith(('http://', 'https://')):
            captcha_url = self.base_url + captcha_url

        # Download captcha image with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.base_url
        }

        response = requests.get(captcha_url, headers=headers, timeout=10)
        response.raise_for_status()

        captcha_image = Image.open(io.BytesIO(response.content))
        print(f"Captcha image size: {captcha_image.size}, mode: {captcha_image.mode}")

        # Save original captcha for debugging
        debug_filename = f"./downloads/captcha_debug_{int(time.time())}.png"
        captcha_image.save(debug_filename)
        print(f"Saved debug captcha: {debug_filename}")

        # Try multiple solving approaches
        return self._solve_captcha_multiple_methods(captcha_image)

    def _solve_canvas_captcha(self, canvas_element):
        """Solve canvas-based captcha"""
        print("Solving canvas-based captcha...")

        try:
            # Get canvas data URL
            canvas_data_url = self.driver.execute_script(
                "return arguments[0].toDataURL('image/png');", canvas_element
            )

            # Convert data URL to image
            import base64
            header, encoded = canvas_data_url.split(',', 1)
            decoded_data = base64.b64decode(encoded)

            captcha_image = Image.open(io.BytesIO(decoded_data))

            # Save original captcha for debugging
            debug_filename = f"./downloads/canvas_captcha_debug_{int(time.time())}.png"
            captcha_image.save(debug_filename)
            print(f"Saved canvas captcha: {debug_filename}")

            return self._solve_captcha_multiple_methods(captcha_image)

        except Exception as e:
            print(f"Canvas captcha processing failed: {e}")
            return None

    def _solve_svg_captcha(self, svg_element):
        """Solve SVG-based captcha"""
        print("Solving SVG-based captcha...")

        try:
            # Get SVG content
            svg_content = self.driver.execute_script(
                "return new XMLSerializer().serializeToString(arguments[0]);", svg_element
            )

            # Save SVG for debugging
            debug_filename = f"./downloads/svg_captcha_debug_{int(time.time())}.svg"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            print(f"Saved SVG captcha: {debug_filename}")

            # For now, try to extract text from SVG
            # This is a simplified approach
            import re
            text_elements = re.findall(r'<text[^>]*>(.*?)</text>', svg_content)
            if text_elements:
                # Remove HTML tags from text
                import html
                cleaned_text = html.unescape(text_elements[0])
                cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
                return self._clean_captcha_text(cleaned_text)

            return None

        except Exception as e:
            print(f"SVG captcha processing failed: {e}")
            return None

    def _solve_div_captcha(self, div_element):
        """Solve div-based or background image captcha"""
        print("Solving div-based captcha...")

        try:
            # Save screenshot for debugging
            screenshot_filename = f"./downloads/captcha_page_debug_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_filename)
            print(f"Saved page screenshot: {screenshot_filename}")

            # Get div element details for debugging
            div_id = div_element.get_attribute('id')
            div_class = div_element.get_attribute('class')
            div_html = div_element.get_attribute('outerHTML')
            div_text = div_element.text.strip()

            print(f"Div details:")
            print(f"  ID: {div_id}")
            print(f"  Class: {div_class}")
            print(f"  Text: '{div_text}'")
            print(f"  HTML length: {len(div_html) if div_html else 0}")

            # Save div HTML for analysis
            html_filename = f"./downloads/captcha_div_debug_{int(time.time())}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(div_html or 'No HTML content')
            print(f"Saved div HTML: {html_filename}")

            # Try to get background image
            bg_image = self.driver.execute_script(
                """
                var element = arguments[0];
                var style = window.getComputedStyle(element);
                return {
                    backgroundImage: style.backgroundImage,
                    background: style.background,
                    backgroundColor: style.backgroundColor,
                    color: style.color,
                    fontSize: style.fontSize,
                    fontFamily: style.fontFamily
                };
                """, div_element
            )

            print(f"Background info: {bg_image}")

            if bg_image.get('backgroundImage') and bg_image['backgroundImage'] != 'none' and 'url(' in bg_image['backgroundImage']:
                # Extract URL from background style
                import re
                url_match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', bg_image['backgroundImage'])
                if url_match:
                    img_url = url_match.group(1)
                    print(f"Found background image URL: {img_url}")

                    # Convert to absolute URL if needed
                    if img_url.startswith('/'):
                        img_url = self.base_url.rstrip('/') + img_url
                    elif not img_url.startswith(('http://', 'https://')):
                        img_url = self.base_url + img_url

                    # Download and process
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': self.base_url
                    }

                    response = requests.get(img_url, headers=headers, timeout=10)
                    response.raise_for_status()

                    captcha_image = Image.open(io.BytesIO(response.content))

                    # Save for debugging
                    debug_filename = f"./downloads/div_captcha_debug_{int(time.time())}.png"
                    captcha_image.save(debug_filename)
                    print(f"Saved div captcha: {debug_filename}")

                    return self._solve_captcha_multiple_methods(captcha_image)

            # Try to get text content of the div (for math captchas)
            if div_text and len(div_text) >= 3:
                print(f"Found div text: '{div_text}'")

                # Check if it's a math expression
                if any(op in div_text for op in ['+', '-', '*', '=', '/', 'plus', 'minus', 'times']):
                    print("Detected math expression in div text")
                    return self._solve_math_expression_text(div_text)

                # Try to extract numbers
                import re
                numbers = re.findall(r'\d+', div_text)
                if numbers:
                    print(f"Extracted numbers: {numbers}")
                    # Try simple math with first two numbers
                    if len(numbers) >= 2:
                        try:
                            num1, num2 = int(numbers[0]), int(numbers[1])
                            # Try different operations
                            possible_results = [str(num1 + num2), str(num1 - num2), str(num1 * num2)]
                            for result in possible_results:
                                if self._validate_captcha_text(result):
                                    print(f"Math result: {result}")
                                    return result
                        except:
                            pass

                # If not math, try text cleaning
                return self._clean_captcha_text(div_text)

            # Try to find all text in the div (including nested elements)
            all_text = self.driver.execute_script(
                "return arguments[0].innerText || arguments[0].textContent;", div_element
            )

            if all_text and len(all_text.strip()) >= 3:
                print(f"Found all text in div: '{all_text}'")
                return self._clean_captcha_text(all_text.strip())

            return None

        except Exception as e:
            print(f"Div captcha processing failed: {e}")
            return None

    def _comprehensive_captcha_analysis(self):
        """Comprehensive analysis to find any captcha-like elements"""
        print("\n=== COMPREHENSIVE CAPTCHA ANALYSIS ===")

        # Save full page source
        html_filename = f"./downloads/full_page_debug_{int(time.time())}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"Full page source saved: {html_filename}")

        # Save current screenshot
        screenshot_filename = f"./downloads/current_page_debug_{int(time.time())}.png"
        self.driver.save_screenshot(screenshot_filename)
        print(f"Current page screenshot saved: {screenshot_filename}")

        # Check all images on the page
        print("\nChecking all images:")
        images = self.driver.find_elements(By.TAG_NAME, "img")
        for i, img in enumerate(images):
            try:
                src = img.get_attribute('src') or 'no-src'
                alt = img.get_attribute('alt') or 'no-alt'
                id_attr = img.get_attribute('id') or 'no-id'
                class_attr = img.get_attribute('class') or 'no-class'
                displayed = img.is_displayed()
                print(f"  Image {i}: src='{src[:50] if len(src) > 50 else src}...', alt='{alt}', id='{id_attr}', displayed={displayed}")
            except:
                print(f"  Image {i}: Error getting details")

        # Check all canvas elements
        print("\nChecking all canvas elements:")
        canvases = self.driver.find_elements(By.TAG_NAME, "canvas")
        for i, canvas in enumerate(canvases):
            try:
                id_attr = canvas.get_attribute('id') or 'no-id'
                class_attr = canvas.get_attribute('class') or 'no-class'
                displayed = canvas.is_displayed()
                width = canvas.get_attribute('width') or 'no-width'
                height = canvas.get_attribute('height') or 'no-height'
                print(f"  Canvas {i}: id='{id_attr}', class='{class_attr}', displayed={displayed}, size={width}x{height}")
            except:
                print(f"  Canvas {i}: Error getting details")

        # Check all divs that might contain captcha-related content
        print("\nChecking div elements with potential captcha content:")
        all_divs = self.driver.find_elements(By.TAG_NAME, "div")
        captcha_like_divs = []

        for div in all_divs:
            try:
                id_attr = div.get_attribute('id') or ''
                class_attr = div.get_attribute('class') or ''
                text = div.text.strip()

                # Look for captcha-like content
                if (any(keyword in id_attr.lower() for keyword in ['captcha', 'code', 'verify', 'securi', 'random']) or
                    any(keyword in class_attr.lower() for keyword in ['captcha', 'code', 'verify', 'securi', 'random']) or
                    any(op in text for op in ['+', '-', '*', '=', '?']) or
                    text and any(char.isdigit() for char in text) and len(text) < 20):

                    displayed = div.is_displayed()
                    style = div.get_attribute('style') or ''
                    bg_image = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).backgroundImage;", div
                    )

                    captcha_like_divs.append({
                        'id': id_attr,
                        'class': class_attr,
                        'text': text,
                        'displayed': displayed,
                        'style': style,
                        'bg_image': bg_image
                    })

                    print(f"  Div candidate: id='{id_attr}', class='{class_attr}', text='{text}', displayed={displayed}, bg_image={bg_image}")

            except:
                continue

        # Check spans with potential content
        print("\nChecking span elements with potential captcha content:")
        spans = self.driver.find_elements(By.TAG_NAME, "span")
        for span in spans:
            try:
                text = span.text.strip()
                id_attr = span.get_attribute('id') or ''
                class_attr = span.get_attribute('class') or ''

                if (any(keyword in id_attr.lower() for keyword in ['captcha', 'code', 'verify', 'securi', 'random']) or
                    any(keyword in class_attr.lower() for keyword in ['captcha', 'code', 'verify', 'securi', 'random']) or
                    any(op in text for op in ['+', '-', '*', '=', '?']) or
                    text and any(char.isdigit() for char in text) and len(text) < 20):

                    displayed = span.is_displayed()
                    print(f"  Span candidate: id='{id_attr}', class='{class_attr}', text='{text}', displayed={displayed}")

            except:
                continue

        # Check JavaScript variables or hidden elements
        print("\nChecking for JavaScript-generated content:")
        try:
            js_content = self.driver.execute_script("""
                // Look for common captcha-related variables or elements
                var results = [];

                // Check window variables
                if (window.captcha) results.push('window.captcha: ' + JSON.stringify(window.captcha));
                if (window.captchaValue) results.push('window.captchaValue: ' + window.captchaValue);
                if (window.captchaAnswer) results.push('window.captchaAnswer: ' + window.captchaAnswer);

                // Check for any math expressions in the document
                var walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                var node;
                while(node = walker.nextNode()) {
                    var text = node.textContent.trim();
                    if (text && (/\\d+\\s*[+\\-*/]\\s*\\d+/.test(text) || /\\d+\\s*[=]\\s*[?]/.test(text))) {
                        results.push('Math expression found: ' + text);
                    }
                }

                return results;
            """)

            if js_content:
                for item in js_content:
                    print(f"  JS analysis: {item}")

        except Exception as e:
            print(f"  JS analysis error: {e}")

        print("=== END COMPREHENSIVE ANALYSIS ===\n")

    def _find_text_captcha(self):
        """Find text-based captcha (math problems, etc.)"""
        print("Looking for text-based captcha...")

        # First try specific selectors
        text_selectors = [
            ".captcha-question",
            "#captcha-question",
            ".captcha-text",
            "#captcha-text",
            "[data-captcha-question]",
            ".math-captcha",
            "#math-captcha",
            ".captcha-label",
            "#captcha-label"
        ]

        for selector in text_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and any(op in text for op in ['+', '-', '*', '=', '?']):
                            print(f"Found text captcha with selector: '{selector}' - '{text}'")
                            return element
            except:
                continue

        # If not found with specific selectors, use comprehensive search
        print("Specific selectors failed, doing comprehensive text search...")

        # Get all elements that might contain text
        all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(),'+') or contains(text(),'-') or contains(text(),'*') or contains(text(),'=') or contains(text(),'?')]")

        for element in all_elements:
            try:
                if element.is_displayed():
                    text = element.text.strip()
                    if text and len(text) < 50:  # Reasonable length for captcha
                        # Check for math expressions
                        import re
                        if re.search(r'\d+\s*[+\-*/]\s*\d+', text) or re.search(r'\d+\s*[=]\s*[?]', text):
                            print(f"Found math expression in element: '{text}'")
                            return element
                        # Also check for simple numbers that might be captcha
                        if any(char.isdigit() for char in text) and len(text) > 1:
                            print(f"Found potential number-based captcha: '{text}'")
                            return element
            except:
                continue

        # If still not found, try JavaScript to get all text nodes
        print("JavaScript-based text search...")
        try:
            math_texts = self.driver.execute_script("""
                var results = [];
                var walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                var node;
                while(node = walker.nextNode()) {
                    var text = node.textContent.trim();
                    if (text && (/\\d+\\s*[+\\-*/]\\s*\\d+/.test(text) || /\\d+\\s*[=]\\s*[?]/.test(text))) {
                        // Get the parent element
                        var parent = node.parentElement;
                        if (parent && window.getComputedStyle(parent).display !== 'none') {
                            results.push({
                                text: text,
                                tagName: parent.tagName,
                                className: parent.className || '',
                                id: parent.id || ''
                            });
                        }
                    }
                }
                return results;
            """)

            if math_texts:
                for item in math_texts:
                    print(f"JavaScript found math: '{item['text']}' in {item['tagName']}.{item['className']}")
                    # Try to find the element by searching for this text
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{item['text']}')]")
                    for element in elements:
                        if element.is_displayed():
                            print(f"Found element for math expression: '{item['text']}'")
                            return element
        except Exception as e:
            print(f"JavaScript text search failed: {e}")

        return None

    def _solve_text_captcha(self, text_element):
        """Solve text-based captcha (math problems)"""
        try:
            text = text_element.text.strip()
            print(f"Solving text captcha: '{text}'")

            # Try to extract and solve math expression
            return self._solve_math_expression_text(text)

        except Exception as e:
            print(f"Text captcha solving failed: {e}")
            return None

    def _solve_math_expression_text(self, text):
        """Solve math expression from text"""
        import re

        print(f"Solving math expression: '{text}'")

        # Clean the text but keep operators
        cleaned_text = text.replace('?', '').replace('=', '').strip()

        # Look for math patterns in order of specificity
        patterns = [
            # Word-based operators (more specific)
            (r'(\d+)\s*times\s*(\d+)', '*'),
            (r'(\d+)\s*multiplied\s*by\s*(\d+)', '*'),
            (r'(\d+)\s*plus\s*(\d+)', '+'),
            (r'(\d+)\s*added\s*to\s*(\d+)', '+'),
            (r'(\d+)\s*minus\s*(\d+)', '-'),
            (r'(\d+)\s*subtracted\s*from\s*(\d+)', '-'),
            (r'(\d+)\s*divided\s*by\s*(\d+)', '/'),

            # Symbol-based operators
            (r'(\d+)\s*\×\s*(\d+)', '*'),  # Unicode multiplication
            (r'(\d+)\s*x\s*(\d+)', '*'),    # Letter x for multiplication
            (r'(\d+)\s*\*\s*(\d+)', '*'),  # Asterisk multiplication
            (r'(\d+)\s*\+\s*(\d+)', '+'),  # Addition
            (r'(\d+)\s*\-\s*(\d+)', '-'),  # Subtraction
            (r'(\d+)\s*\/\s*(\d+)', '/'),  # Division
        ]

        for pattern, operator in patterns:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                num1, num2 = int(match.group(1)), int(match.group(2))

                if operator == '+':
                    result = num1 + num2
                    op_symbol = '+'
                elif operator == '-':
                    result = num1 - num2
                    op_symbol = '-'
                elif operator == '*':
                    result = num1 * num2
                    op_symbol = '×'
                elif operator == '/':
                    result = num1 // num2 if num2 != 0 else 0
                    op_symbol = '÷'

                print(f"Math expression solved: {num1} {op_symbol} {num2} = {result}")
                return str(result)

        # If no clear math expression found, try to extract and process digits
        digits = re.findall(r'\d+', text)  # Get full numbers, not individual digits
        if digits:
            print(f"Extracted numbers: {digits}")

            # If we have exactly 2 numbers, try simple operations
            if len(digits) == 2:
                num1, num2 = int(digits[0]), int(digits[1])
                print(f"Trying operations with {num1} and {num2}")

                # Check if text suggests multiplication
                if any(word in text.lower() for word in ['times', 'multiply', 'x', '×']):
                    result = num1 * num2
                    print(f"Assumed multiplication: {num1} × {num2} = {result}")
                    return str(result)
                # Check if text suggests addition
                elif any(word in text.lower() for word in ['plus', 'add', '+']):
                    result = num1 + num2
                    print(f"Assumed addition: {num1} + {num2} = {result}")
                    return str(result)
                # Default to first number for simple captchas
                else:
                    print(f"Defaulting to first number: {num1}")
                    return str(num1)

            # If we have one number, return it
            elif len(digits) == 1:
                result = digits[0]
                print(f"Single number found: {result}")
                return result

            # Multiple numbers, return the first
            else:
                result = digits[0]
                print(f"Multiple numbers found, using first: {result}")
                return result

        print("No math expression could be solved")
        return None

    def _solve_captcha_multiple_methods(self, captcha_image):
        """Try multiple captcha solving methods"""
        methods = [
            ("Basic OCR", self._solve_basic_ocr),
            ("Enhanced OCR", self._solve_enhanced_ocr),
            ("Math Expression", self._solve_math_expression),
            ("Pattern Recognition", self._solve_pattern_recognition)
        ]

        for method_name, method_func in methods:
            try:
                print(f"Trying {method_name} method...")
                result = method_func(captcha_image.copy())  # Use copy to avoid modifying original

                if result and self._validate_captcha_text(result):
                    print(f"✓ {method_name} successful: '{result}'")
                    return result

            except Exception as e:
                print(f"✗ {method_name} failed: {e}")
                continue

        return None

    def _solve_basic_ocr(self, captcha_image):
        """Basic OCR with Tesseract"""
        # Convert to grayscale
        if captcha_image.mode != 'L':
            captcha_image = captcha_image.convert('L')

        # Basic preprocessing
        captcha_image = captcha_image.resize((captcha_image.width * 2, captcha_image.height * 2), Image.Resampling.LANCZOS)

        # Extract text
        config = '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        text = pytesseract.image_to_string(captcha_image, config=config)
        return self._clean_captcha_text(text)

    def _solve_enhanced_ocr(self, captcha_image):
        """Enhanced OCR with better preprocessing"""
        # Convert to grayscale
        if captcha_image.mode != 'L':
            captcha_image = captcha_image.convert('L')

        # Apply threshold
        from PIL import ImageFilter
        captcha_image = captcha_image.filter(ImageFilter.SHARPEN)

        # Resize for better OCR
        width, height = captcha_image.size
        captcha_image = captcha_image.resize((width * 3, height * 3), Image.Resampling.LANCZOS)

        # Try different PSM modes
        psm_modes = [7, 8, 6, 13, 11]  # Single text line, single word, etc.
        whitelist = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

        for psm in psm_modes:
            try:
                config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist={whitelist}'
                text = pytesseract.image_to_string(captcha_image, config=config)
                cleaned_text = self._clean_captcha_text(text)

                if self._validate_captcha_text(cleaned_text):
                    return cleaned_text
            except:
                continue

        return None

    def _solve_math_expression(self, captcha_image):
        """Solve math-based captcha expressions"""
        # Convert to grayscale
        if captcha_image.mode != 'L':
            captcha_image = captcha_image.convert('L')

        # Resize for better OCR
        captcha_image = captcha_image.resize((captcha_image.width * 2, captcha_image.height * 2), Image.Resampling.LANCZOS)

        # Try to detect math expressions
        math_config = '--psm 7 -c tessedit_char_whitelist=0123456789+-*=() '
        text = pytesseract.image_to_string(captcha_image, config=math_config)
        text = self._clean_captcha_text(text)

        # Try to evaluate if it's a math expression
        if self._is_math_expression(text):
            try:
                # Safely evaluate math expression
                result = eval(text)
                return str(int(result))  # Return integer result
            except:
                pass

        # Try digit recognition for simple answers
        digit_config = '--psm 8 -c tessedit_char_whitelist=0123456789'
        digits = pytesseract.image_to_string(captcha_image, config=digit_config)
        return self._clean_captcha_text(digits)

    def _solve_pattern_recognition(self, captcha_image):
        """Pattern-based captcha solving using image processing"""
        import numpy as np

        # Convert to numpy array
        if captcha_image.mode != 'L':
            captcha_image = captcha_image.convert('L')

        img_array = np.array(captcha_image)

        # Try to detect simple patterns or characters
        # This is a simplified pattern matching approach
        patterns = {
            '0': np.array([[1,1,1],[1,0,1],[1,1,1]]),
            '1': np.array([[0,1,0],[1,1,0],[0,1,0]]),
            '2': np.array([[1,1,1],[0,1,0],[1,1,1]]),
            '3': np.array([[1,1,1],[0,1,0],[1,1,1]]),
            '4': np.array([[1,0,1],[1,1,1],[0,0,1]]),
            '5': np.array([[1,1,1],[1,0,0],[1,1,1]]),
            '6': np.array([[1,1,1],[1,0,0],[1,1,1]]),
            '7': np.array([[1,1,1],[0,0,1],[0,0,1]]),
            '8': np.array([[1,1,1],[1,0,1],[1,1,1]]),
            '9': np.array([[1,1,1],[1,0,1],[1,1,1]])
        }

        # Simple threshold
        threshold = 128
        binary = (img_array > threshold).astype(int)

        # Try to match patterns (simplified approach)
        detected_chars = []
        # This is a very basic implementation - in practice, you'd need more sophisticated pattern matching
        # For now, fall back to OCR with different approach

        return None  # Fall back to other methods

    def _clean_captcha_text(self, text):
        """Clean and validate captcha text"""
        if not text:
            return ""

        # Remove whitespace and common OCR artifacts
        text = text.strip().replace(" ", "").replace("\n", "").replace("\t", "")

        # Remove common OCR mistakes
        text = text.replace("|", "1").replace("l", "1").replace("I", "1").replace("O", "0").replace("o", "0")
        text = text.replace("S", "5").replace("s", "5").replace("Z", "2").replace("z", "2")
        text = text.replace("G", "6").replace("g", "9").replace("B", "8").replace("b", "8")

        # Remove any non-alphanumeric characters except common ones
        import re
        text = re.sub(r'[^0-9A-Za-z\+\-\*\=]', '', text)

        return text

    def _validate_captcha_text(self, text):
        """Validate if captcha text looks reasonable"""
        if not text or len(text) < 3:
            return False

        # Check if text contains reasonable characters
        import re
        if not re.match(r'^[0-9A-Za-z\+\-\*\=]+$', text):
            return False

        # Check if it's not all the same character (likely OCR error)
        if len(set(text)) == 1 and len(text) > 1:
            return False

        return True

    def _is_math_expression(self, text):
        """Check if text looks like a math expression"""
        import re
        # Simple pattern to detect math expressions like "5+3", "10-2", etc.
        math_pattern = r'^\d+[\+\-\*\/]\d+$'
        return bool(re.match(math_pattern, text))

    def _manual_captcha_fallback(self):
        """Manual captcha entry fallback"""
        try:
            # Try to display captcha to user
            captcha_files = [f for f in os.listdir("./downloads") if "captcha_debug" in f]
            if captcha_files:
                latest_captcha = max(captcha_files, key=lambda x: os.path.getctime(f"./downloads/{x}"))
                print(f"Latest captcha saved as: ./downloads/{latest_captcha}")
                print("Please check the captcha image in the downloads folder.")

            print("\n⚠ AUTOMATIC CAPTCHA SOLVING FAILED ⚠")
            print("Manual captcha entry required.")
            print("Options:")
            print("1. Enter captcha manually")
            print("2. Open browser to view captcha")
            print("3. Skip and try again")

            choice = input("Choose option (1/2/3): ").strip()

            if choice == "1":
                return input("Enter captcha text manually: ").strip()
            elif choice == "2":
                # Save current page HTML for inspection
                with open("./downloads/captcha_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("Page HTML saved to ./downloads/captcha_page.html")
                print("Opening browser for captcha inspection...")
                input("After viewing captcha, press Enter and enter the text:")
                return input("Enter captcha text: ").strip()
            else:
                print("Skipping captcha attempt...")
                return None

        except Exception as e:
            print(f"Error in manual fallback: {e}")
            return input("Final fallback - Enter captcha manually: ").strip()

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

        if not captcha_text:
            print("⚠ No captcha solution obtained, attempting manual entry...")
            captcha_text = input("Enter captcha manually (or press Enter to skip): ").strip()

        if not captcha_text:
            print("Skipping captcha, attempting login without it...")
            # Try to find and click login button directly
            self._attempt_login_without_captcha()
            return

        # Enhanced captcha field handling
        captcha_field = self._find_captcha_field()

        if captcha_field:
            try:
                # Remove any readonly attributes
                self.driver.execute_script("""
                    var captchaField = arguments[0];
                    captchaField.removeAttribute('readonly');
                    captchaField.removeAttribute('disabled');
                    captchaField.focus();
                """, captcha_field)

                # Clear and fill captcha field
                captcha_field.clear()
                time.sleep(0.5)
                captcha_field.send_keys(captcha_text)
                print(f"✓ Captcha filled successfully: '{captcha_text}'")

                # Verify captcha was entered
                entered_value = captcha_field.get_attribute('value')
                if entered_value == captcha_text:
                    print("✓ Captcha value verified")
                else:
                    print(f"⚠ Captcha value mismatch. Expected: '{captcha_text}', Got: '{entered_value}'")

                # Click login button with enhanced handling
                self._click_login_button_enhanced()

            except Exception as e:
                print(f"⚠ Error filling captcha: {e}")
                # Try alternative approach
                self._alternative_captcha_entry(captcha_text)
        else:
            raise Exception("Could not find captcha field with any method")

    def _find_captcha_field(self):
        """Enhanced captcha field finding with multiple selectors and contexts"""
        captcha_selectors = [
            # Primary selectors based on common captcha field names
            (By.NAME, "captcha"),
            (By.NAME, "captcha_answer"),
            (By.NAME, "captchacode"),
            (By.NAME, "captcha_code"),
            (By.NAME, "verification"),
            (By.NAME, "verify"),
            (By.NAME, "security_code"),

            # ID selectors
            (By.ID, "captcha"),
            (By.ID, "captcha_answer"),
            (By.ID, "captchacode"),
            (By.ID, "captcha_code"),
            (By.ID, "verification"),
            (By.ID, "verify"),
            (By.ID, "security_code"),

            # CSS selectors
            (By.CSS_SELECTOR, "input[name*='captcha']"),
            (By.CSS_SELECTOR, "input[id*='captcha']"),
            (By.CSS_SELECTOR, "input[placeholder*='captcha']"),
            (By.CSS_SELECTOR, "input[placeholder*='Captcha']"),
            (By.CSS_SELECTOR, "input[aria-label*='captcha']"),
            (By.CSS_SELECTOR, ".captcha input"),
            (By.CSS_SELECTOR, "#captcha input"),

            # XPath selectors for more specific finding
            (By.XPATH, "//input[contains(@name, 'captcha')]"),
            (By.XPATH, "//input[contains(@id, 'captcha')]"),
            (By.XPATH, "//input[contains(@placeholder, 'captcha')]"),
            (By.XPATH, "//input[contains(@placeholder, 'Captcha')]"),

            # More generic approaches
            (By.CSS_SELECTOR, "input[type='text'][maxlength='6']"),
            (By.CSS_SELECTOR, "input[type='text'][maxlength='5']"),
            (By.CSS_SELECTOR, "input[type='text'][maxlength='8']"),
            (By.XPATH, "//input[@type='text' and string-length(@value) <= 8]"),
        ]

        # Try in current context first
        print("Looking for captcha field in current context...")
        captcha_field = self._try_selectors(captcha_selectors)
        if captcha_field:
            print(f"✓ Found captcha field in current context: {captcha_field.get_attribute('name') or captcha_field.get_attribute('id')}")
            return captcha_field

        # If not found, try different iframe contexts
        print("Captcha field not found, trying iframe contexts...")
        return self._find_captcha_in_iframes(captcha_selectors)

    def _try_selectors(self, selectors, context="current"):
        """Try multiple selectors to find captcha field"""
        for by_type, selector in selectors:
            try:
                element = self.driver.find_element(by_type, selector)
                if element and element.is_displayed():
                    print(f"  ✓ Found with {by_type}: {selector}")
                    return element
            except Exception as e:
                continue
        return None

    def _find_captcha_in_iframes(self, selectors):
        """Find captcha field in iframes"""
        try:
            # Get all iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Checking {len(iframes)} iframes for captcha field...")

            for i, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    time.sleep(0.5)  # Wait for iframe content

                    captcha_field = self._try_selectors(selectors, f"iframe {i}")
                    if captcha_field:
                        print(f"✓ Found captcha field in iframe {i}")
                        self.found_captcha_in_iframe = True
                        self.captcha_iframe_index = i
                        return captcha_field

                    self.driver.switch_to.default_content()
                except Exception as e:
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    continue

        except Exception as e:
            print(f"Error searching iframes: {e}")

        return None

    def _click_login_button_enhanced(self):
        """Enhanced login button clicking with multiple approaches"""
        login_selectors = [
            # Primary selectors
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[value*='Login']"),
            (By.CSS_SELECTOR, "button:contains('Login')"),
            (By.CSS_SELECTOR, "input[value*='Masuk']"),
            (By.CSS_SELECTOR, "button:contains('Masuk')"),
            (By.CSS_SELECTOR, "input[value*='Submit']"),
            (By.CSS_SELECTOR, "button:contains('Submit')"),

            # XPath selectors
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[contains(@value, 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//input[contains(@value, 'Masuk')]"),
            (By.XPATH, "//button[contains(text(), 'Masuk')]"),
            (By.XPATH, "//input[contains(@value, 'Submit')]"),
            (By.XPATH, "//button[contains(text(), 'Submit')]"),

            # Class-based selectors
            (By.CSS_SELECTOR, ".btn-login"),
            (By.CSS_SELECTOR, ".login-btn"),
            (By.CSS_SELECTOR, ".submit-btn"),
            (By.CSS_SELECTOR, ".btn-primary"),

            # ID-based selectors
            (By.ID, "login"),
            (By.ID, "submit"),
            (By.ID, "login-btn"),
            (By.ID, "submit-btn"),
        ]

        print("Looking for login button...")
        login_button = self._try_selectors(login_selectors)

        if login_button:
            try:
                # Ensure button is clickable
                self.driver.execute_script("""
                    var btn = arguments[0];
                    btn.scrollIntoView(true);
                    btn.style.display = 'block';
                    btn.style.visibility = 'visible';
                    btn.disabled = false;
                """, login_button)

                time.sleep(1)

                # Try clicking with different methods
                try:
                    login_button.click()
                    print("✓ Login button clicked (standard click)")
                    return
                except:
                    # Try JavaScript click
                    self.driver.execute_script("arguments[0].click();", login_button)
                    print("✓ Login button clicked (JavaScript click)")
                    return

            except Exception as e:
                print(f"⚠ Error clicking login button: {e}")

        # Fallback: try to submit the form
        print("Login button not found, trying form submission...")
        try:
            login_form = self.driver.find_element(By.TAG_NAME, "form")
            self.driver.execute_script("arguments[0].submit();", login_form)
            print("✓ Form submitted successfully")
        except Exception as e:
            print(f"⚠ Form submission failed: {e}")
            raise Exception("Could not click login button or submit form")

    def _attempt_login_without_captcha(self):
        """Attempt login without captcha if captcha solving fails"""
        print("Attempting login without captcha...")

        # This would be used in cases where captcha might not be required
        # or as a fallback mechanism
        try:
            self._click_login_button_enhanced()
            print("✓ Login attempt without captcha completed")
            time.sleep(3)
        except Exception as e:
            print(f"⚠ Login without captcha failed: {e}")
            raise Exception("Login failed - captcha required but not provided")

    def _alternative_captcha_entry(self, captcha_text):
        """Alternative method for entering captcha"""
        print("Trying alternative captcha entry methods...")

        # Try finding by visible text or pattern
        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

        for input_elem in all_inputs:
            try:
                input_type = input_elem.get_attribute('type') or 'text'
                input_name = input_elem.get_attribute('name') or ''
                input_id = input_elem.get_attribute('id') or ''
                placeholder = input_elem.get_attribute('placeholder') or ''

                # Look for input that might be captcha field
                if (input_type == 'text' and
                    ('captcha' in input_name.lower() or 'captcha' in input_id.lower() or
                     'captcha' in placeholder.lower() or 'verif' in input_name.lower() or
                     'code' in input_name.lower())):

                    if input_elem.is_displayed():
                        print(f"Found potential captcha field: name='{input_name}', id='{input_id}'")
                        input_elem.clear()
                        input_elem.send_keys(captcha_text)
                        print("✓ Captcha entered via alternative method")

                        self._click_login_button_enhanced()
                        return

            except Exception as e:
                continue

        print("⚠ Alternative captcha entry failed")
        raise Exception("Could not find captcha field with any method")

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
            # Keep browser open for inspection (commented out for automatic testing)
            # input("Press Enter to close browser...")
            self.driver.quit()

def main():
    """Main function to run the automation"""
    print("eCampuz Portal Automation")
    print("=" * 40)

    # Set headless to False for testing
    headless = False

    # Create and run automation
    automation = EcampuzAutomation(headless=headless)
    automation.run_automation()

if __name__ == "__main__":
    main()