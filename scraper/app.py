from daraz_scraper import DarazScraper

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