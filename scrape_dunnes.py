#Deliverable: iteration 3
# Version 3.0
#Date: 13/01/2025

# code taken and adapted from scrape_supervalu.py

import requests
import mysql.connector
import re

# store id and categories being scraped
store_id = 409
category_ids = [
    ("50066", "Fresh Food"),
    ("47183", "Fresh Food"),
    ("47181", "Fresh Food"),
    ("50101", "Fresh Food"),
    ("53421", "Fresh Food"),
    ("47171", "Bakery & Deli"),
    ("49703", "Bakery & Deli"),
    ("47199", "Bakery & Deli"),
    ("47197", "Bakery & Deli"),
    ("47173", "Chilled & Frozen"),
    ("47185", "Chilled & Frozen"),
    ("47193", "Health, Beauty & Baby"),
    ("47169", "Health, Beauty & Baby"),
    ("47201", "Health, Beauty & Baby"),
    ("53021", "Health, Beauty & Baby"),
    ("47175", "Drinks & Alcohol"),
    ("47203", "Drinks & Alcohol"),
    ("47177", "Food Cupboard"),
    ("47191", "Food Cupboard"),
    ("47189", "Household & Pets"),
    ("47195", "Household & Pets"),
    ("47187", "Household & Pets"),
    ("54441", "Household & Pets"),

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
    "Referer": "https://www.dunnesstoresgrocery.com/",
    "Origin": "https://www.dunnesstoresgrocery.com/"
}

store_regions = {
    409: "Dunnes Douglas Cork",
}

def get_store_region():
    return store_regions.get(store_id, "")

def scrape_dunnes():
    all_products = []

    # get store region through id
    region = get_store_region()
    print(f"Using Store Region: {region}")

    for category_id, category_name in category_ids:
        print(f"\n Scraping {category_name}...")
        api_url = f"https://storefrontgateway.dunnesstoresgrocery.com/api/stores/{store_id}/categories/{category_id}/search"
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
                    "retailer": "Dunnes",
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
        retailer = "Dunnes"

        if not name or not price:
            continue

        cur.execute("""SELECT id FROM product WHERE name = %s AND retailer = %s AND region = %s """, (name, retailer, region))
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
        data = scrape_dunnes()
        save_to_db(data)
    except Exception as e:
        print(" Error during scrape:", e)

# end of code block for iteration 3 deliverable