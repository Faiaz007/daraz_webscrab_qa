from bs4 import BeautifulSoup
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
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def extract_product_info_bs4(self, card):
        """Extract product information using BeautifulSoup"""
        try:
            title_tag = card.select_one('a[title]')
            title = title_tag['title'] if title_tag else card.select_one('div[class*="RfADt"]').text.strip()
        except:
            title = "No title"

        try:
            price_tag = card.select_one('span[class*="ooOxS"], div[class*="aBrP0"]')
            price = price_tag.text.strip() if price_tag else "No price"
        except:
            price = "No price"

        try:
            link_tag = card.select_one('a[href*="/products/"]')
            link = link_tag['href'] if link_tag else "No link"
            if link.startswith("/"):
                link = "https://www.daraz.com.bd" + link
        except:
            link = "No link"

        try:
            image_tag = card.select_one('img[src*="img.crd.lazcdn.com"]')
            image_url = image_tag['src'] if image_tag else "No image"
        except:
            image_url = "No image"

        try:
            rating_tag = card.select_one('span[class*="oa6ri"]')
            rating = rating_tag['title'] if rating_tag else "No rating"
        except:
            rating = "No rating"

        return {
            "Title": title,
            "Price": price,
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
            max_scroll_attempts = 7

            while len(products) < self.max_products and scroll_attempts < max_scroll_attempts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2.5, 4.5))  

             
                soup = BeautifulSoup(self.driver.page_source, "lxml")
                cards = soup.select('div[data-qa-locator="product-item"]')

                for card in cards[len(products):]:
                    product = self.extract_product_info_bs4(card)
                    if product not in products:
                        products.append(product)
                    if len(products) >= self.max_products:
                        break

                scroll_attempts += 1

            os.makedirs("scraper/data", exist_ok=True)
            with open("scraper/data/last_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

        finally:
            self.driver.quit()
        return products

    def save_data(self, products, csv_path="scraper/data/laptops.csv", json_path="scraper/data/laptops.json"):
        try:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df = pd.DataFrame(products)
            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient="records")
            print(f"Saved {len(products)} products to {csv_path} and {json_path}")
        except Exception as e:
            print(f"Failed to save data: {e}")

class DarazScraperApp:
    def __init__(self, search_url="https://www.daraz.com.bd/catalog/?q=laptop", max_products=40):
        self.scraper = DarazScraper(search_url, max_products)

    def run(self):
        print("Starting Daraz Scraper...")
        products = self.scraper.scrape_laptops()

        if products:
            self.scraper.save_data(products)
            print("Scraping completed successfully.")
        else:
            print("No products found.")

if __name__ == "__main__":
    app = DarazScraperApp(search_url="https://www.daraz.com.bd/catalog/?q=laptop", max_products=40)
    app.run()