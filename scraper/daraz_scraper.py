from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import time
import random


class DarazScraper:
    def __init__(self, search_url="https://www.daraz.com.bd/catalog/?q=laptop", max_products=40):
        self.search_url = search_url
        self.max_products = max_products
        self.driver = None

    def initialize_driver(self):
        """Initialize and configure the Selenium WebDriver"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu") 
        options.add_argument("--disable-software-rasterizer")  
        options.add_argument("--disable-extensions")  
        options.add_argument("--disable-webgl")  
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        self.driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def extract_product_info(self, card):
        """Extract the product information from each product card"""
        try:
            title = card.find_element(By.CSS_SELECTOR, 'a[title]').get_attribute('title')
        except:
            title = card.find_element(By.CSS_SELECTOR, 'div[class*="RfADt"]').text

        try:
            price = card.find_element(By.CSS_SELECTOR, 'span[class*="ooOxS"]').text
        except:
            price = card.find_element(By.CSS_SELECTOR, 'div[class*="aBrP0"]').text

        link = card.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]').get_attribute('href')

        try:
            image_url = card.find_element(By.CSS_SELECTOR, 'img[src*="img.crd.lazcdn.com"]').get_attribute('src')
        except:
            image_url = "No image"

        try:
            rating = card.find_element(By.CSS_SELECTOR, 'span[class*="oa6ri"]').get_attribute('title')
        except:
            rating = "No rating"

        return {
            "Title": title.strip(),
            "Price": price.strip(),
            "Rating": rating,
            "Product Link": link,
            "Image URL": image_url
        }

    def scrape_laptops(self):
        self.initialize_driver()
        products = []
        try:
            self.driver.get(self.search_url)
            scroll_attempts = 0
            max_scroll_attempts = 5

            while len(products) < self.max_products and scroll_attempts < max_scroll_attempts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))

                cards = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-qa-locator="product-item"]')

                for card in cards[len(products):]:
                    product = self.extract_product_info(card)
                    if product not in products:
                        products.append(product)
                    if len(products) >= self.max_products:
                        break

                scroll_attempts += 1

        finally:
            self.driver.quit()

        return products

    def save_data(self, products, csv_path="scraper/data/laptops.csv", json_path="scraper/data/laptops.json"):
        """Save the scraped product data into CSV and JSON files"""
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df = pd.DataFrame(products)
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient="records")
        print(f"Saved {len(products)} products to {csv_path} and {json_path}")

