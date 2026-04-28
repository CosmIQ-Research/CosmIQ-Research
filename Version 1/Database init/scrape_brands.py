from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import random
import time

def generate_brand_id(existing):
    while True:
        bid = f"{random.randint(0, 9999999999):010d}"
        if bid not in existing:
            existing.add(bid)
            return bid

def scrape_all_brands(driver):
    driver.get("https://www.ulta.com/brand/all")
    print(driver.page_source[:5000])  # print first 5000 chars of page HTML  
    time.sleep(10)  # Allow page to fully load

    all_brands = set()
    actions = ActionChains(driver)

    # Locate letter buttons (A-Z, #)
    letter_buttons = driver.find_elements(By.CSS_SELECTOR, "ul.BrandLogoList__nav li a")
    print(f"Found {len(letter_buttons)} letter tabs.")

    for letter in letter_buttons:
        try:
            actions.move_to_element(letter).click().perform()
            time.sleep(10)  # Wait for brands list to update
            # Get brands under the selected letter
            brands = driver.find_elements(By.CSS_SELECTOR, "span.pal-c-Link__label")
            for b in brands:
                text = b.text.strip()
                if text:
                    all_brands.add(text)
            print(f"Scraped letter: {letter.text}, brands so far: {len(all_brands)}")
        except Exception as e:
            print(f"Error scraping letter {letter.text}: {e}")

    return all_brands

def main():
    options = Options()
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    brands = scrape_all_brands(driver)
    driver.quit()

    existing_ids = set()
    brand_data = [{"brand_id": generate_brand_id(existing_ids), "name": name} for name in sorted(brands)]
    df = pd.DataFrame(brand_data)
    df.to_csv("ulta_brands.csv", index=False)
    print(f"Extracted {len(df)} brands across A-Z and saved to ulta_brands.csv")

if __name__ == "__main__":
    main()
