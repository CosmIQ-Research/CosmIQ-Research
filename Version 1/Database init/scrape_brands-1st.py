import requests
from bs4 import BeautifulSoup
import pandas as pd
import random

def generate_brand_id(existing_ids):
    while True:
        bid = f"{random.randint(0, 9999999999):010d}"
        if bid not in existing_ids:
            existing_ids.add(bid)
            return bid

def scrape_ulta_brands():
    url = "https://www.ulta.com/brand/all"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    brand_elems = soup.select("span.pal-c-Link__label")
    brands = {elem.get_text(strip=True) for elem in brand_elems if elem.get_text(strip=True)}
    return brands

def main():
    brands = scrape_ulta_brands()
    existing_ids = set()
    brand_data = [{"brand_id": generate_brand_id(existing_ids), "name": name} for name in sorted(brands)]
    df = pd.DataFrame(brand_data)
    df.to_csv("ulta_brands.csv", index=False)
    print(f"Extracted {len(df)} brands and saved to ulta_brands.csv")

if __name__ == "__main__":
    main()
