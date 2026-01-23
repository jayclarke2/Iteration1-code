#Deliverable: iteration 3
# Version 3.0
#Date: 13/01/2025

#code adapted from existing code in scrape_supervalu.py

import requests
import mysql.connector
import re

# store id and categories being scraped
store_id = 260
category_ids = [
    ("O100001", "Fresh Food"),            # fruit and veg
    ("O100017", "Fresh Food"),            # fish and seafood
    ("O100015", "Fresh Food"),            # meat and poultry
    ("O100010", "Bakery & Deli"),         # bakery
    ("O100020", "Bakery & Deli"),         # deli
    ("O100023", "Dairy & Eggs"),          # cheese
    ("O100025", "Dairy & Eggs"),          # milk, butter, eggs
    ("O100027", "Health, Beauty & Baby"), # health and wellness
    ("O100030", "Chilled & Frozen"),      # chilled food
    ("O100035", "Food Cupboard"),         # food cupboard
    ("O100045", "Chilled & Frozen"),      # frozen food
    ("O100050", "Drinks & Alcohol"),      # drinks
    ("O100055", "Health, Beauty & Baby"), # beauty & personal care
    ("O100060", "Health, Beauty & Baby"), # baby
    ("O100065", "Household & Pets"),      # household
    ("O100070", "Household & Pets"),      # pets
    ("O100075", "Drinks & Alcohol"),      # alcohol
]
items_per_page = 48

# database connection
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "FYP",
    "database": "fyp_grocery"
}

# API headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://shop.supervalu.ie/",
    "Origin": "https://shop.supervalu.ie"
}

store_regions = {
    260: "Quish's Supervalu Ballincollig Cork",
}

def get_store_region():
    return store_regions.get(store_id, "")

def scrape_supervalu():
    all_products = []

    # get store region through id
    region = get_store_region()
    print(f"Using Store Region: {region}")

    for category_id, category_name in category_ids:
        print(f"\n Scraping {category_name}...")
        api_url = f"https://storefrontgateway.supervalu.ie/api/stores/{store_id}/categories/{category_id}/search"
        page = 1
        total_fetched = 0

        while True:
            params = {
                "take": items_per_page,
                "skip": (page - 1) * items_per_page,
                "page": page
            }

            resp = requests.get(api_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                print("Request failed with status:", resp.status_code)
                break

            data = resp.json()
            items = data.get("items", [])
            if not items:
                print("No more products found in", category_name)
                break

            # get product name
            for item in items:
                name = item.get("name") or item.get("productName")

                # get product price
                price_data = item.get("price")
                if isinstance(price_data, dict):
                    price = (
                        price_data.get("current")
                        or price_data.get("display")
                        or price_data.get("priceLabel")
                    )
                else:
                    price = str(price_data)

                if price:
                    for bad in ["€", "/kg", "kg", "avg/ea", "/ea", "/piece", "/pc", "/pkt"]:
                        price = price.replace(bad, "")
                    price = price.strip()
                    match = re.search(r"[\d\.]+", price)
                    price = match.group(0) if match else None

                #get image url
                image_url = ""
                images = item.get("images")
                if isinstance(images, dict):
                    image_url = (
                        images.get("main")
                        or images.get("thumbnail")
                        or images.get("default")
                        or images.get("medium")
                        or ""
                    )
                elif isinstance(images, list) and len(images) > 0:
                    first = images[0]
                    if isinstance(first, dict):
                        image_url = first.get("url") or first.get("main") or first.get("thumbnail") or ""
                elif "image" in item:
                    img = item["image"]
                    if isinstance(img, dict):
                        image_url = img.get("url") or img.get("default") or img.get("main") or ""
                    else:
                        image_url = str(img)

                all_products.append({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "retailer": "Supervalu",
                    "category": category_name,
                    "region": region
                })

                print(f"{name} — €{price} — {image_url if image_url else 'No image'} — {region}")
                total_fetched += 1

            if len(items) < items_per_page:
                break
            page += 1

        print(f" Done scraping {category_name}: {total_fetched} items.")

    return all_products


def save_to_db(products):
    print("\n Saving data to MySQL...")
    db = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor()

    inserted = 0
    updated = 0

    for p in products:
        name = p.get("name")
        price = p.get("price")
        image_url = p.get("image_url")
        category = p.get("category")
        region = p.get("region")
        retailer = "Supervalu"

        if not name or not price:
            continue

        cur.execute("""SELECT id FROM product WHERE name = %s AND retailer = %s AND region = %s""", (name, retailer, region))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE product
                SET price = %s,
                    image_url = %s,
                    category = %s,
                    region = %s,
                    retailer = %s,
                    last_updated = NOW()
                WHERE id = %s
            """, (price, image_url, category, region, retailer, existing[0]))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO product (name, price, image_url, category, region, retailer, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (name, price, image_url, category, region, retailer))
            inserted += 1

    db.commit()
    cur.close()
    db.close()

    print(f" Database updated: {inserted} new, {updated} updated.")
    print("Done! Data saved to MySQL.")


if __name__ == "__main__":
    try:
        data = scrape_supervalu()
        save_to_db(data)
    except Exception as e:
        print(" Error during scrape:", e)

# end of code block for iteration 3 deliverable