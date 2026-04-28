import psycopg
import json

# === Build connection string ===
conn_str = (
    "postgresql://neondb_owner:npg_o0HsChQ4lkSa"
    "@ep-holy-unit-a5k4mdnx-pooler.us-east-2.aws.neon.tech/neondb"
    "?sslmode=require&options=endpoint%3Dep-holy-unit-a5k4mdnx-pooler"
)

# === Load Data ===
with open("products_ulta.json") as f:
    products = json.load(f)

with open("ingredients_inci.json") as f:
    ingredients = json.load(f)

# === Index ingredients by name for fast lookup ===
ing_lookup = {i['name'].lower(): i for i in ingredients}

# === Connect to PostgreSQL ===
with psycopg.connect(conn_str) as conn:
    with conn.cursor() as cur:

        # === Insert Brands (fallback to name if brand missing) ===
        brand_names = list(set([p['brand'] if p['brand'] else p['name'] for p in products if p.get('name')]))
        cur.execute("SELECT name FROM brands")
        existing_brands = [b[0] for b in cur.fetchall()]

        for brand in brand_names:
            if brand not in existing_brands:
                cur.execute("INSERT INTO brands (name) VALUES (%s)", (brand,))

        conn.commit()

        # === Fetch brand IDs ===
        cur.execute("SELECT brand_id, name FROM brands")
        brand_map = {name: bid for bid, name in cur.fetchall()}

        # === Insert Ingredients ===
        cur.execute("SELECT inci_name FROM ingredients")
        existing_inci = [i[0].lower() for i in cur.fetchall()]

        inserted_ingredients = {}
        for ing in ingredients:
            name = ing['name'].lower()
            if name not in existing_inci:
                cur.execute("""
                    INSERT INTO ingredients (inci_name, common_names, toxicity_score, carcinogenic_flag)
                    VALUES (%s, %s, %s, %s) RETURNING ingredient_id
                """, (ing['name'], [ing['name']], None, bool(ing['concern'])))
                ing_id = cur.fetchone()[0]
                inserted_ingredients[name] = ing_id
            else:
                cur.execute("SELECT ingredient_id FROM ingredients WHERE LOWER(inci_name) = %s", (name,))
                ing_id = cur.fetchone()[0]
                inserted_ingredients[name] = ing_id

        conn.commit()

        # === Insert Products ===
        cur.execute("SELECT name FROM products")
        existing_products = [p[0] for p in cur.fetchall()]

        for prod in products:
            if prod['name'] not in existing_products:
                ingredient_ids = [inserted_ingredients.get(i.strip().lower()) for i in prod['ingredients'] if i.strip().lower() in inserted_ingredients]
                ingredient_ids = list(filter(None, ingredient_ids))
                brand_key = prod['brand'] if prod['brand'] else prod['name']
                cur.execute("""
                    INSERT INTO products (brand_id, name, category, ingredients, is_clean_labeled)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    brand_map.get(brand_key),
                    prod['name'],
                    prod.get('category'),
                    ingredient_ids,
                    None
                ))

        conn.commit()

print("Data inserted into PostgreSQL.")
