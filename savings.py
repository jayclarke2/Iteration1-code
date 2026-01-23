#Deliverable: iteration 3
# Version 3.0
#Date: 17/01/2026

# user story 16 - see savings summary
# code aided from ChatGPT - Appendix D - Iteration 3 report

from app import get_db
import re

retailers = ["Aldi", "Dunnes", "Supervalu"]

# remove filler words in products for better matching
stop_words = {"fresh", "pack", "packs", "large", "small", "medium", "value", "club", "brand", "new", "extra", "original", "classic", "family", "size", "the", "and", "with", "for", "of"}

def keywords(name: str, max_words: int = 4):
    s = (name or "").lower()

    # remove sizes/units
    s = re.sub(r"\b\d+(\.\d+)?\s?(g|kg|ml|l|litre|litres|lb|oz)\b", " ", s)
    s = re.sub(r"\b\d+\s?(pack|pk)\b", " ", s)

    # remove punctuation
    s = re.sub(r"[^a-z\s]", " ", s)

    words = [w for w in s.split() if len(w) > 2 and w not in stop_words]
    return words[:max_words]

def find_similar_price(cur, retailer: str, item_name: str, item_price: float):
    words = keywords(item_name, max_words=4)
    if not words:
        return None

    # Price matches
    low = max(0.01, float(item_price) * 0.75)
    high = float(item_price) * 1.50

    def run_query(joiner: str):
        likes = f" {joiner} ".join(["name LIKE %s"] * len(words))
        params = [retailer] + [f"%{w}%" for w in words] + [low, high]

        cur.execute(f"""
            SELECT price FROM product WHERE retailer = %s AND ({likes}) AND price BETWEEN %s AND %s ORDER BY price ASC LIMIT 1""", params)
        row = cur.fetchone()
        return float(row["price"]) if row else None

    price = run_query("AND")
    if price is not None:
        return price

    return run_query("OR")

def basket_savings_summary(cart_items, current_retailer):
    if not cart_items or not current_retailer:
        return {}

    current_total = round(sum(i["price"] * i["quantity"] for i in cart_items), 2)

    db = get_db()
    cur = db.cursor(dictionary=True)

    summary = {}

    for r in retailers:
        if r == current_retailer:
            continue

        other_total = 0.0
        missing = 0

        for item in cart_items:
            item_name = item.get("name", "")
            item_price = float(item.get("price", 0.0))
            qty = int(item.get("quantity", 1))

            match_price = find_similar_price(cur, r, item_name, item_price)
            if match_price is None:
                missing += 1
                continue

            other_total += match_price * qty

        if missing > 0:
            summary[r] = {"missing": missing}
        else:
            other_total = round(other_total, 2)
            summary[r] = {"total": other_total, "diff": round(other_total - current_total, 2), "missing": 0}

    cur.close()
    db.close()

    return {"current_total": current_total, "current_retailer": current_retailer, "others": summary}

# user story 18 - split store savings - code adapted from existing code above
def split_store_best_total(cart_items):
    if not cart_items:
        return {"total": 0.0, "missing": 0}

    db = get_db()
    cur = db.cursor(dictionary=True)

    total = 0.0
    missing = 0

    for item in cart_items:
        name = item.get("name", "")
        price = float(item.get("price", 0.0))
        qty = int(item.get("quantity", 1))

        best_price = None

        for r in retailers:
            match_price = find_similar_price(cur, r, name, price)
            if match_price is None:
                continue
            if best_price is None or match_price < best_price:
                best_price = match_price

        if best_price is None:
            missing += 1
            continue

        total += best_price * qty

    cur.close()
    db.close()

    return {"total": round(total, 2), "missing": missing}

# end of code block for iteration 3 deliverable