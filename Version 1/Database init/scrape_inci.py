import requests
from bs4 import BeautifulSoup
import json
import time
import re

SEARCH_URL = "https://incibeauty.com/en/search?search={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def clean_ingredient_name(name):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s\-]+", "", name)  # remove punctuation
    name = re.sub(r"may contain.*", "", name)     # remove "may contain" trails
    return name.strip()

def fetch_inci_details(ingredient):
    query = ingredient.replace(" ", "+")
    url = SEARCH_URL.format(query)
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, 'html.parser')

    result = soup.find("a", class_="list-group-item")
    if not result:
        return {"name": ingredient, "url": None, "description": None, "concern": None}

    detail_url = "https://incibeauty.com" + result['href']
    detail_resp = requests.get(detail_url, headers=HEADERS)
    detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')

    description = None
    concern = None
    try:
        description_tag = detail_soup.find("div", class_="card-body")
        if description_tag:
            description = description_tag.text.strip()
    except:
        pass

    try:
        risk_tag = detail_soup.find("div", class_="alert-danger")
        if risk_tag:
            concern = risk_tag.text.strip()
    except:
        pass

    return {
        "name": ingredient,
        "url": detail_url,
        "description": description,
        "concern": concern
    }

def load_ulta_ingredients(file_path="products_ulta.json"):
    with open(file_path, "r") as f:
        products = json.load(f)

    all_ingredients = set()
    for prod in products:
        for ing in prod.get("ingredients", []):
            clean = clean_ingredient_name(ing)
            if clean:
                all_ingredients.add(clean)

    return list(all_ingredients)

def main():
    ingredients = load_ulta_ingredients()
    print(f"{len(ingredients)} unique cleaned ingredients found.")

    enriched = []
    for ing in ingredients:
        print(f"Fetching: {ing}")
        enriched.append(fetch_inci_details(ing))
        time.sleep(2)

    with open("ingredients_inci.json", "w") as f:
        json.dump(enriched, f, indent=2)

    print("Saved to ingredients_inci.json")

if __name__ == "__main__":
    main()
