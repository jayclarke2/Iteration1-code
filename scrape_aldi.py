#Deliverable: iteration 3
# Version 3.0
#Date: 06/01/2026

#code adapted from existing code in scrape_supervalu.py
#code aided and adapted from ChatGPT see appendix A - Iteration 3 Report

import re
import time
import requests
import mysql.connector
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# configuration
BASE = "https://www.aldi.ie"
REGION = "Aldi Douglas Cork"
RETAILER = "Aldi"

ALDI_CATEGORIES = [
    ("Chilled & Frozen", "https://www.aldi.ie/products/frozen-food/k/1588161416978081"),
    ("Fresh Food", "https://www.aldi.ie/products/fresh-food/k/1588161416978075"),
    ("Fresh Food", "https://www.aldi.ie/products/higher-protein-food-drink/k/1588161424510128"),
    ("Fresh Food", "https://www.aldi.ie/products/vegetarian-plant-based/k/1588161421881175"),
    ("Bakery & Deli", "https://www.aldi.ie/products/bakery/k/1588161416978074"),
    ("Chilled & Frozen", "https://www.aldi.ie/products/chilled-food/k/1588161416978076"),
    ("Food Cupboard", "https://www.aldi.ie/products/food-cupboard/k/1588161416978078"),
    ("Food Cupboard", "https://www.aldi.ie/products/back-to-school-meals/k/1588161426199273"),
    ("Drinks & Alcohol", "https://www.aldi.ie/products/drinks/k/1588161416978079"),
    ("Drinks & Alcohol", "https://www.aldi.ie/products/alcohol/k/1588161416978080"),
    ("Health, Beauty & Baby", "https://www.aldi.ie/products/health-beauty/k/1588161416978083"),
    ("Health, Beauty & Baby", "https://www.aldi.ie/products/baby-toddler/k/1588161416978082"),
    ("Household & Pets", "https://www.aldi.ie/products/home-cleaning/k/1588161416978084"),
    ("Household & Pets", "https://www.aldi.ie/products/pet-care/k/1588161416978085")
]

REQUEST_DELAY_SECONDS = 0.2
ITEM_LIMIT_PER_CATEGORY = None

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "FYP",
    "database": "fyp_grocery",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE + "/",
}

# helpers and headers
def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def normalize_url(href: str) -> str:
    return urljoin(BASE, href)


def is_same_path(base_url: str, candidate_url: str) -> bool:
    b = urlparse(base_url)
    c = urlparse(candidate_url)
    return (b.netloc == c.netloc) and (b.path == c.path)


def clean_price(text: str):
    if not text:
        return None

    # Find all € amounts
    matches = list(re.finditer(r"€\s*([0-9]+(?:\.[0-9]{1,2})?)", text))
    if not matches:
        return None

    normal_prices = []
    for m in matches:
        value = m.group(1)

        after = text[m.end(): m.end() + 8]
        if "/" in after:
            continue

        normal_prices.append(value)

    if normal_prices:
        return normal_prices[-1]

    return matches[-1].group(1)


# scrape category url pages
def crawl_category_for_product_links(category_url: str):
    to_visit = [category_url]
    visited = set()
    product_links = set()

    while to_visit:
        page_url = to_visit.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)

        soup = get_soup(page_url)

        # Collect product detail
        for a in soup.select("a[href^='/product/']"):
            product_links.add(normalize_url(a["href"]))

        # Find pagination
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            full = normalize_url(href)

            if is_same_path(category_url, full) and full not in visited and full not in to_visit:
                txt = a.get_text(strip=True)
                if "page" in full.lower() or (txt.isdigit() and len(txt) <= 3):
                    to_visit.append(full)

        time.sleep(REQUEST_DELAY_SECONDS)

    return sorted(product_links)


# parse product name
def parse_product(product_url: str):
    soup = get_soup(product_url)

    # get product name
    h1 = soup.find("h1")
    name = h1.get_text(" ", strip=True) if h1 else None

    # get product price
    page_text = soup.get_text(" ", strip=True)
    price = clean_price(page_text)

    # get image url
    image_url = ""
    og = soup.select_one('meta[property="og:image"]')
    if og and og.get("content"):
        image_url = og["content"].strip()

    return name, price, image_url


# scrape all categories
def scrape_aldi_all_categories():
    if not ALDI_CATEGORIES:
        raise ValueError("ALDI_CATEGORIES is empty. Add (category_name, category_url) pairs.")

    all_products = []
    seen = set()

    for category_name, category_url in ALDI_CATEGORIES:
        if not category_url or "PASTE_URL_HERE" in category_url:
            print(f"Skipping category '{category_name}' - URL not set.")
            continue

        print(f"\n=== Scraping {RETAILER} - {category_name} ===")
        print(f"Category URL: {category_url}")

        product_urls = crawl_category_for_product_links(category_url)
        print(f"Found {len(product_urls)} product URLs.")

        scraped_this_category = 0

        for i, url in enumerate(product_urls, start=1):
            if ITEM_LIMIT_PER_CATEGORY is not None and scraped_this_category >= ITEM_LIMIT_PER_CATEGORY:
                print(f"Reached ITEM_LIMIT_PER_CATEGORY={ITEM_LIMIT_PER_CATEGORY} for {category_name}.")
                break

            try:
                name, price, image_url = parse_product(url)

                if not name or not price:
                    print(f"[{i}/{len(product_urls)}] Skipped (missing name/price): {url}")
                    continue

                key = (name, price, image_url, category_name)
                if key in seen:
                    continue
                seen.add(key)

                all_products.append({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "category": category_name,
                    "region": REGION,
                    "retailer": RETAILER,
                })

                scraped_this_category += 1
                print(f"[{i}/{len(product_urls)}] {name} — €{price}")

            except Exception as e:
                print(f"[{i}/{len(product_urls)}] Error parsing {url}: {e}")

            time.sleep(REQUEST_DELAY_SECONDS)

        print(f"Done {category_name}: scraped {scraped_this_category} items.")

    print(f"\nTotal scraped across all categories: {len(all_products)}")
    return all_products


# save scrape to database
def save_to_db(products):
    print("\nSaving data to MySQL...")
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
        retailer = p.get("retailer")

        if not name or not price:
            continue

        # product match with retailer to prevent overwrite
        cur.execute("SELECT id FROM product WHERE name = %s AND retailer = %s", (name, retailer))
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

    print(f"Database updated: {inserted} new, {updated} updated.")
    print("Done! Data saved to MySQL.")


if __name__ == "__main__":
    try:
        data = scrape_aldi_all_categories()
        save_to_db(data)
    except Exception as e:
        print("Error during Aldi scrape:", e)

# end of code block for iteration 3 deliverable