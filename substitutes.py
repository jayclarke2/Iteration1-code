#Deliverable: iteration 4
# Version 4.0
#Date: 31/01/2026

# code below aided from ChatGPT see Appendix E - iteration 3 report

from flask import session, render_template, redirect, url_for, request
from app import app, get_db
import re

# remove unneccassary words from product names
filler_words = {"and", "or", "with", "without", "the", "a", "an", "of", "for", "to", "pack", "pk", "x", "fresh", "new", "family", "value", "large", "small", "medium", "approx"
}

# use key product words
def keywords(name: str):
    if not name:
        return []

    s = name.lower()

    # remove sizes from product name
    s = re.sub(r"\b\d+(\.\d+)?\s?(g|kg|ml|l|ltr|litre|oz|lb|pack|pk)\b", " ", s)
    s = re.sub(r"\b\d+\s?x\s?\d+\b", " ", s)
    # remove punctuation
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    parts = [p for p in s.split() if p and p not in filler_words]

    # keep key words
    parts = [p for p in parts if len(p) >= 3]

    return parts[:4]


@app.route("/substitutes/<int:product_id>")
def substitutes(product_id):
    retailer = session.get("basket_retailer")
    region = session.get("basket_region")

    if not retailer or not region:
        return redirect(url_for("basket"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Original product
    cur.execute("""SELECT id, name, category, price, image_url FROM product WHERE id = %s"""
    , (product_id,))
    original = cur.fetchone()

    if not original:
        cur.close()
        db.close()
        return redirect(url_for("basket"))

    # substitute within 30 percent of original price
    band = 0.30
    min_price = float(original["price"]) * (1 - band)
    max_price = float(original["price"]) * (1 + band)

    keys = keywords(original["name"])

    # SQL
    sql = """SELECT id, name, price, image_url FROM product WHERE retailer = %s AND region = %s AND category = %s AND id <> %s AND price BETWEEN %s AND %s"""
    params = [retailer, region, original["category"], product_id, min_price, max_price]

    # need 2 keywords from product
    for k in keys:
        sql += " AND name LIKE %s"
        params.append(f"%{k}%")

    # find closest equivalents
    sql += " ORDER BY ABS(price - %s) ASC LIMIT 5"
    params.append(float(original["price"]))

    cur.execute(sql, params)
    subs = cur.fetchall()

    cur.close()
    db.close()

    return render_template("substitutes.html", original=original, subs=subs)

# end of code block for iteration 4 deliverable