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

def get_ulta_brands(driver):
    url = "https://www.ulta.com/brand/all#/"
    driver.get(url)
    time.sleep(3)

    brands = set()
    letters = driver.find_elements(By.CSS_SELECTOR, "ul.BrandLogoList__nav li a")
    actions = ActionChains(driver)

    for letter in letters:
        try:
            actions.move_to_element(letter).click().perform()
            time.sleep(2)
            brand_elems = driver.find_elements(By.CSS_SELECTOR, "a.BrandLogoList__brandName")
            for elem in brand_elems:
                text = elem.text.strip()
                if text:
                    brands.add(text)
        except Exception as e:
            print(f"Error on letter: {letter.text}, {e}")
    
    return brands

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    brands = get_ulta_brands(driver)
    driver.quit()

    existing_ids = set()
    data = [{"brand_id": generate_brand_id(existing_ids), "name": name} for name in sorted(brands)]
    df = pd.DataFrame(data)
    df.to_csv("ulta_brands.csv", index=False)
    print(f"Extracted {len(df)} brands and saved to ulta_brands.csv")

if __name__ == "__main__":
    main()
