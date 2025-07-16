from selenium import webdriver
from selenium.webdriver.chrome.service import Service # For specifying chromedriver path
from selenium.webdriver.common.by import By # For locating elements
from selenium.webdriver.support.ui import WebDriverWait # For explicit waits
from selenium.webdriver.support import expected_conditions as EC # For conditions in waits
from bs4 import BeautifulSoup # For parsing HTML
import requests # For downloading external CSS files
import os # For creating directories and file paths

# --- Configuration ---
# 1. Replace with the actual path to your chromedriver executable
# Example for Windows: CHROMEDRIVER_PATH = r"C:\path\to\your\chromedriver.exe"
# Example for Linux/macOS: CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CHROMEDRIVER_PATH = "C:\WebDriver\chromedriver.exe"

# 2. The URL of the website you want to scrape (a JS-heavy example is good)
TARGET_URL = "https://ethicent.com/" # Replace with a dynamic website if testing JS rendering

# 3. Directory to save extracted files
OUTPUT_DIR = "extracted_website_content"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

def setup_driver():
    """Configures and returns a headless Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser without GUI
    options.add_argument("--disable-gpu") # Recommended for headless mode
    options.add_argument("--no-sandbox") # Recommended for containerized environments
    options.add_argument("--window-size=1920x1080") # Set a consistent window size
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # Add more options for stealth if needed (e.g., to avoid bot detection)

    try:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized successfully (headless Chrome).")
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        print("Please ensure chromedriver is installed and its path is correct,")
        print("and that its version matches your Chrome browser version.")
        return None

def extract_html_and_css(driver, url):
    """
    Navigates to the URL, waits for dynamic content, extracts HTML,
    downloads linked CSS, and extracts computed styles.
    """
    print(f"\n--- Processing: {url} ---")
    try:
        driver.get(url)

        # --- Handling Dynamic Content: Waiting Strategies ---
        # This is CRUCIAL for JavaScript-heavy websites.
        # You need to wait until the content you're interested in has loaded.

        # Strategy 1: Wait for a specific element to be present/visible/clickable
        # Replace 'body' with a more specific CSS selector if you know what dynamic element to wait for.
        # Example: EC.presence_of_element_located((By.ID, "app-root"))
        print("Waiting for page content to load (waiting for body tag)...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Page body loaded.")

        # Strategy 2: Wait for network idle (often good for single-page applications)
        # This waits until there are no more network requests for a short period.
        # This is not directly a Selenium `EC` but can be implemented with a short sleep
        # or more complex network monitoring in advanced setups.
        # For simple cases, explicit waits for elements are often enough.
        # For truly complex AJAX loads, you might need short `time.sleep()` after initial waits
        # or analyze network requests via browser's dev tools for specific endpoints.
        # time.sleep(3) # A small additional pause if content is very slow to render after initial DOM.

        # --- Extract Rendered HTML ---
        rendered_html = driver.page_source
        html_file_path = os.path.join(OUTPUT_DIR, "index.html")
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        print(f"Rendered HTML saved to: {html_file_path}")

        # --- Extract Linked CSS Files ---
        print("Searching for and downloading linked CSS files...")
        soup = BeautifulSoup(rendered_html, 'html.parser')
        linked_css_tags = soup.find_all('link', rel='stylesheet')
        css_downloaded_count = 0
        for link_tag in linked_css_tags:
            css_href = link_tag.get('href')
            if css_href:
                # Resolve relative URLs
                if not css_href.startswith(('http://', 'https://')):
                    css_url = requests.compat.urljoin(url, css_href)
                else:
                    css_url = css_href

                try:
                    css_response = requests.get(css_url, timeout=10)
                    css_response.raise_for_status() # Raise an exception for HTTP errors
                    css_filename = os.path.basename(css_url.split('?')[0]) # Remove query params for filename
                    css_file_path = os.path.join(OUTPUT_DIR, css_filename if css_filename else "style.css") # Default name if no filename

                    with open(css_file_path, "wb") as f:
                        f.write(css_response.content)
                    print(f"Downloaded CSS: {css_filename}")
                    css_downloaded_count += 1
                except requests.exceptions.RequestException as req_err:
                    print(f"Failed to download CSS from {css_url}: {req_err}")
                except Exception as e:
                    print(f"An unexpected error occurred while downloading CSS from {css_url}: {e}")

        print(f"Finished downloading {css_downloaded_count} linked CSS files.")

        # --- Adjusting CSS link paths in HTML (YOUR CODE GOES HERE) ---
        print("Adjusting CSS link paths in HTML...")
        for link_tag in soup.find_all('link', rel='stylesheet'):
            css_href = link_tag.get('href')
            if css_href:
                original_filename = os.path.basename(css_href.split('?')[0])
                if original_filename:
                    link_tag['href'] = original_filename # Change href to just the filename
                else:
                    # Handle cases where URL doesn't end in a clear filename, default
                    link_tag['href'] = "style.css" # Or a similar default name you used
        print(f"Adjusted CSS link paths in HTML.")

        # --- Save the MODIFIED HTML ---
        # This is where the HTML with adjusted CSS links is finally saved
        html_file_path = os.path.join(OUTPUT_DIR, "index.html")
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(str(soup)) # Save the modified soup object back to string
        print(f"Modified HTML saved to: {html_file_path}")

        # --- Extract Embedded CSS (within <style> tags) ---
        print("Extracting embedded CSS...")
        embedded_css_tags = soup.find_all('style')
        embedded_css_count = 0
        for i, style_tag in enumerate(embedded_css_tags):
            if style_tag.string:
                style_content = style_tag.string
                embedded_css_file_path = os.path.join(OUTPUT_DIR, f"embedded_style_{i}.css")
                with open(embedded_css_file_path, "w", encoding="utf-8") as f:
                    f.write(style_content)
                print(f"Extracted embedded CSS to: embedded_style_{i}.css")
                embedded_css_count += 1
        print(f"Finished extracting {embedded_css_count} embedded CSS blocks.")

        # --- Extract Inline CSS and Computed Styles (more advanced) ---
        print("\nAttempting to extract computed styles for some elements...")
        # This requires iterating through elements and executing JavaScript on them.
        # Let's pick a few common elements as an example.
        elements_to_inspect = [
            (By.TAG_NAME, "body"),
            (By.TAG_NAME, "h1"),
            (By.TAG_NAME, "p"),
            (By.CSS_SELECTOR, "a:not([style])") # All links that don't have inline style
        ]

        # Define common CSS properties you might be interested in
        common_css_properties = [
            'color', 'background-color', 'font-size', 'font-family',
            'margin-top', 'margin-bottom', 'padding-top', 'padding-bottom',
            'width', 'height', 'display', 'position', 'left', 'top'
        ]

        extracted_computed_styles = {}

        for by_type, selector in elements_to_inspect:
            try:
                elements = driver.find_elements(by_type, selector)
                if elements:
                    print(f"  Found {len(elements)} elements for selector: {selector}")
                    for i, element in enumerate(elements[:3]): # Limit to first 3 to avoid excessive output
                        element_tag_name = element.tag_name
                        element_id = element.get_attribute('id')
                        element_class = element.get_attribute('class')
                        element_text = element.text[:50].replace('\n', ' ') + '...' if element.text else ''

                        element_info = f"<{element_tag_name}"
                        if element_id: element_info += f" id='{element_id}'"
                        if element_class: element_info += f" class='{element_class}'"
                        element_info += f"> ('{element_text}')"

                        # Use JavaScript to get computed styles
                        computed_style = driver.execute_script(
                            """
                            var elem = arguments[0];
                            if (!elem) return null;
                            var style = window.getComputedStyle(elem);
                            var styles = {};
                            for (var i = 0; i < style.length; i++) {
                                var prop = style[i];
                                styles[prop] = style.getPropertyValue(prop);
                            }
                            return styles;
                            """,
                            element
                        )
                        if computed_style:
                            print(f"    Computed styles for {element_info}:")
                            # Filter for common properties or print all if needed
                            for prop in common_css_properties:
                                if prop in computed_style:
                                    print(f"      - {prop}: {computed_style[prop]}")
                            extracted_computed_styles[f"{selector}_{i}"] = {
                                "element_info": element_info,
                                "styles": computed_style
                            }
                else:
                    print(f"  No elements found for selector: {selector}")
            except Exception as e:
                print(f"  Error processing selector {selector}: {e}")

        # You can save `extracted_computed_styles` to a JSON file if needed.
        # import json
        # with open(os.path.join(OUTPUT_DIR, "computed_styles.json"), "w", encoding="utf-8") as f:
        #     json.dump(extracted_computed_styles, f, indent=4)
        # print("Computed styles extracted and saved (uncomment to enable).")

    except Exception as e:
        print(f"An error occurred during extraction for {url}: {e}")
    finally:
        print(f"--- Finished processing: {url} ---")


# --- Main Execution ---
if __name__ == "__main__":
    driver = None
    try:
        driver = setup_driver()
        if driver:
            extract_html_and_css(driver, TARGET_URL)
    finally:
        if driver:
            driver.quit()
            print("WebDriver session closed.")