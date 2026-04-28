from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time

PRODUCT_URLS = [
    "https://www.ulta.com/p/translucent-loose-setting-powder-pimprod2012342?sku=2569835",
    "https://www.ulta.com/p/luxe-pro-powder-xlsImpprod15971019?sku=2509740",
    "https://www.ulta.com/p/camo-liquid-blush-pimprod2042954?sku=2617738",
    "https://www.ulta.com/p/cheeks-out-freestyle-cream-blush-pimprod2031376?sku=2592449",
    "https://www.ulta.com/p/performer-skin-focused-foundation-pimprod2043010?sku=2618930",
    "https://www.ulta.com/p/keep-me-covered-long-lasting-foundation-pimprod2037417?sku=2603101",
    "https://www.ulta.com/p/born-this-way-super-coverage-multi-use-concealer-xlsImpprod18631033?sku=2529024",
    "https://www.ulta.com/p/instant-age-rewind-eraser-dark-circle-treatment-concealer-xlsImpprod3490149?sku=2547762",
    "https://www.ulta.com/p/macximal-silky-matte-lipstick-pimprod2043558?sku=2635484",
    "https://www.ulta.com/p/suede-matte-lipstick-lightweight-vegan-lipstick-xlsImpprod18521011?sku=2530262"
]


options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920x1080')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_product_page(url):
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product = {
        "url": url,
        "image": None,
        "ingredients": [],
        "brand": None,
        "name": None,
        "category": None
    }

    try:
        product['name'] = soup.find("h1").text.strip()
    except:
        pass

    try:
        brand_tag = soup.find("a", class_="Link-ds Link-ds--brand")
        if brand_tag:
            product['brand'] = brand_tag.text.strip()
    except:
        pass

    try:
        img_tag = soup.find("img", class_="Image Image--fadeIn")
        if img_tag:
            product['image'] = img_tag['src']
    except:
        pass

    try:
        ingredients_header = soup.find("h3", string=lambda s: s and "Ingredients" in s)
        if ingredients_header:
            ingredients_text = ingredients_header.find_next("p").get_text(strip=True)
            product['ingredients'] = [i.strip() for i in ingredients_text.split(',')]
    except:
        pass

    return product


def main():
    scraped_data = []

    for url in PRODUCT_URLS:
        print(f"Scraping {url}")
        data = scrape_product_page(url)
        scraped_data.append(data)
        time.sleep(2)

    with open("products_ulta.json", "w") as f:
        json.dump(scraped_data, f, indent=2)

    print("Saved to products_ulta.json")
    driver.quit()


if __name__ == "__main__":
    main()