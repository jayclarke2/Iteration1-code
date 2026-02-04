# Deliverable: iteration 4
# Version 4.0
# Date 02/02/2026

#Code adapted from existing code in saved_baskets.py

from flask import render_template, redirect, url_for, session, flash
from app import app, get_db

def require_login():
    return session.get("user_id") is not None and session.get("username") is not None

@app.route("/saved_basket/<int:basket_id>")
def view_saved_basket(basket_id):
    if not require_login():
        flash("Log in to view saved baskets.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # load saved basket of the user
    cur.execute("""SELECT id, name, retailer, region, created_at FROM saved_baskets WHERE id = %s AND user_id = %s""", (basket_id, session["user_id"]))
    basket = cur.fetchone()

    if not basket:
        cur.close(); db.close()
        flash("Saved basket not found.", "error")
        return redirect(url_for("saved_baskets"))

    # basket items
    cur.execute("""SELECT product_id, name, price, quantity, retailer, region FROM saved_basket_items WHERE basket_id = %s ORDER BY id ASC""", (basket_id,))
    items = cur.fetchall()

    cur.close()
    db.close()

    return render_template("saved_basket_items.html", basket=basket, items=items)


@app.route("/add_saved_item/<int:basket_id>/<int:product_id>", methods=["POST"])
def add_saved_item(basket_id, product_id):
    if not require_login():
        flash("Log in to use saved baskets.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ensure the saved basket belongs to the user
    cur.execute("""SELECT id FROM saved_baskets WHERE id = %s AND user_id = %s""", (basket_id, session["user_id"]))
    owned = cur.fetchone()

    if not owned:
        cur.close(); db.close()
        flash("Saved basket not found.", "error")
        return redirect(url_for("saved_baskets"))

    # Pull the item row from saved basket items
    cur.execute("""SELECT product_id, name, price, quantity, retailer, region FROM saved_basket_items WHERE basket_id = %s AND product_id = %s LIMIT 1""", (basket_id, product_id))
    row = cur.fetchone()

    cur.close()
    db.close()

    if not row:
        flash("Item not found in saved basket.", "error")
        return redirect(url_for("view_saved_basket", basket_id=basket_id))

    # basket store lock for single basket
    locked_retailer = session.get("basket_retailer")
    locked_region = session.get("basket_region")

    item_retailer = row.get("retailer")
    item_region = row.get("region")

    # If current basket is, lock it to the added item's store
    if not locked_retailer and not locked_region:
        session["basket_retailer"] = item_retailer
        session["basket_region"] = item_region
    else:
        if locked_retailer != item_retailer or locked_region != item_region:
            flash("Your current basket is locked to a different store/region. Clear basket to switch.", "danger")
            return redirect(url_for("basket"))

    # Add to session cart
    cart = session.get("cart", {})
    pid = str(row["product_id"])

    if pid in cart:
        cart[pid]["quantity"] = int(cart[pid].get("quantity", 1)) + int(row.get("quantity", 1))
    else:
        cart[pid] = {
            "id": int(row["product_id"]),
            "name": row.get("name"),
            "price": float(row.get("price", 0)),
            "quantity": int(row.get("quantity", 1)),
            "retailer": item_retailer,
            "region": item_region,
        }

    session["cart"] = cart
    session.modified = True

    flash("Item added to your current basket.", "success")
    return redirect(url_for("basket"))

# end of code block for iteration 4 deliverable