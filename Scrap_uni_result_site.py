import sys
# sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import re
import os

class CGPAScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver for Google Colab"""
        chrome_options = Options()
        
        # Colab-specific options
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        user_data_dir = f'/tmp/chrome_user_data_{int(time.time())}'
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        try:
            # self.driver = webdriver.Chrome('chromedriver', options=chrome_options)
            self.driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)
            self.driver.implicitly_wait(10)
            print("Chrome driver setup successful!")
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")

            try:
                chrome_options.add_argument('--disable-javascript')  # Remove this line
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
                print("Chrome driver setup successful with alternative options!")
            except Exception as e2:
                print(f"Alternative setup also failed: {e2}")
                raise
    
    def scrape_cgpa(self, roll_number, batch="2025"):
        """
        Scrape CGPA for a given roll number using Selenium
        """
        try:
            print(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            wait = WebDriverWait(self.driver, 15)
            
            self.driver.save_screenshot('/content/page_loaded.png')
            print("Page loaded, screenshot saved")
            
            try:
                print("Looking for batch dropdown...")
                batch_dropdown = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
                select = Select(batch_dropdown)
                select.select_by_value(batch)
                print(f"Selected batch: {batch}")
                time.sleep(1)
            except TimeoutException:
                print(f"Warning: Could not find batch dropdown for roll {roll_number}")
                try:
                    batch_dropdown = self.driver.find_element(By.CSS_SELECTOR, "select")
                    select = Select(batch_dropdown)
                    select.select_by_value(batch)
                    print(f"Found batch dropdown with alternative selector")
                except:
                    print("Could not find batch dropdown at all")
            
            print("Looking for roll number input...")
            roll_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Enter Roll No"]'))
            )
            
            roll_input.clear()
            roll_input.send_keys(str(roll_number))
            print(f"Entered roll number: {roll_number}")
            
            self.driver.save_screenshot('/content/before_search.png')
            
            print("Looking for search button...")
            search_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]"))
            )
            search_button.click()
            print("Clicked search button")
            
            print("Waiting for results...")
            time.sleep(3) 
            
            self.driver.save_screenshot('/content/after_search.png')
            
            try:
                result_section = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.result-section"))
                )
                print("Found result section")
                time.sleep(2)
                
                cgpa_table = self.driver.find_element(By.CSS_SELECTOR, "table.cgpa-table")
                print("Found CGPA table")
                
                cgpa_row = cgpa_table.find_element(By.CSS_SELECTOR, "tr.cgpa-highlight")
                print("Found CGPA highlight row")
                
                td_elements = cgpa_row.find_elements(By.TAG_NAME, "td")
                print(f"Found {len(td_elements)} td elements in GPA row")
                
                for i, td in enumerate(td_elements):
                    print(f"TD {i}: '{td.text.strip()}'")
                
                cgpa_value = None
                for i, td in enumerate(td_elements):
                    td_text = td.text.strip().upper()
                    if 'CGPA' in td_text:
                        if i + 1 < len(td_elements):
                            cgpa_text = td_elements[i + 1].text.strip()
                            print(f"Found GPA text: '{cgpa_text}'")
                            cgpa_match = re.search(r'(\d+\.?\d*)', cgpa_text)
                            if cgpa_match:
                                cgpa_value = float(cgpa_match.group(1))
                                print(f"Extracted GPA value: {cgpa_value}")
                            break
                
                if cgpa_value is None and len(td_elements) >= 2:
                    print("Trying alternative GPA extraction...")
                    for i, td in enumerate(td_elements):
                        td_text = td.text.strip()
                        cgpa_match = re.search(r'^(\d+\.?\d*)$', td_text)
                        if cgpa_match:
                            potential_cgpa = float(cgpa_match.group(1))
                            if 0 <= potential_cgpa <= 10:
                                cgpa_value = potential_cgpa
                                print(f"Found GPA using alternative method: {cgpa_value}")
                                break
                
                if cgpa_value is not None:
                    return {
                        'roll_number': roll_number,
                        'gpa': cgpa_value,
                        'status': 'success'
                    }
                else:
                    return {
                        'roll_number': roll_number,
                        'gpa': None,
                        'status': 'cgpa_value_not_found'
                    }
                    
            except TimeoutException:
                print("Result section not found within timeout")
                try:
                    page_source = self.driver.page_source
                    if 'not found' in page_source.lower() or 'no result' in page_source.lower():
                        return {
                            'roll_number': roll_number,
                            'gpa': None,
                            'status': 'no_result_found'
                        }
                except:
                    pass
                
                return {
                    'roll_number': roll_number,
                    'gpa': None,
                    'status': 'result_section_not_loaded'
                }
                
        except TimeoutException as e:
            print(f"Timeout error: {e}")
            return {
                'roll_number': roll_number,
                'gpa': None,
                'status': f'timeout_error: {str(e)}'
            }
        except Exception as e:
            print(f"General error: {e}")
            return {
                'roll_number': roll_number,
                'gpa': None,
                'status': f'error: {str(e)}'
            }
    
    def scrape_multiple_roll_numbers(self, roll_numbers, batch="2025", delay=3):
        """
        Scrape CGPA for multiple roll numbers
        """
        results = []
        
        for i, roll_number in enumerate(roll_numbers):
            print(f"\n{'='*50}")
            print(f"Processing roll number {roll_number} ({i+1}/{len(roll_numbers)})")
            print(f"{'='*50}")
            
            result = self.scrape_cgpa(roll_number, batch)
            results.append(result)
            
            print(f"Result - Roll: {roll_number}, GPA: {result['gpa']}, Status: {result['status']}")
            
            if i < len(roll_numbers) - 1:
                print(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return results
    
    def save_to_excel(self, results, filename='/content/cgpa_results.xlsx'):
        """
        Save results to Excel file
        """
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)
        print(f"Results saved to {filename}")
        return filename
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



def main():
    BASE_URL = "https://igdtuw-result.vercel.app/result-analysis"  # Replace with the actual URL
    
    # roll_numbers = [
    #     "11401032021",
    #     "11501032021", 
    #     "11601032021",
    #     # Add more roll numbers here
    # ]
    roll_numbers = [f"{i:03}01032021" for i in range(1, 161)]

    try:
        with CGPAScraper(BASE_URL) as scraper:
            print("Starting GPA scraping...")
            results = scraper.scrape_multiple_roll_numbers(roll_numbers, batch="2025", delay=4)
            
            filename = scraper.save_to_excel(results)
            
            successful_results = [r for r in results if r['status'] == 'success']
            print(f"\n{'='*60}")
            print(f"SCRAPING COMPLETED!")
            print(f"{'='*60}")
            print(f"Total roll numbers processed: {len(roll_numbers)}")
            print(f"Successful results: {len(successful_results)}")
            print(f"Results saved to: {filename}")
            
            print(f"\nDETAILED RESULTS:")
            print(f"{'='*60}")
            for result in results:
                print(f"Roll: {result['roll_number']:<12} | GPA: {result['gpa']:<6} | Status: {result['status']}")
            
            return results
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    print("Setting up environment for Google Colab...")
    results = main()