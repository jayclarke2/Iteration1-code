#Deliverable: iteration 2
# Version 2.0
#Date: 17/11/2025
from flask import session, redirect, url_for, render_template
from app import app, get_db, request

#code below adapted from IS3312 Project Phase 2
from flask import session, redirect, url_for, render_template, request
from app import app, get_db

#code adapted from IS3312 Project Phase 2 - cart.py
class Cart:
    def __init__(cart):
        cart.items = session.get("cart", {})

    def add(cart, prod_id, name, price, quantity=1):
        pid = str(prod_id)

        if pid in cart.items:
            cart.items[pid]["quantity"] += quantity
        else:
            cart.items[pid] = {
                "name": name,
                "price": float(price),
                "quantity": quantity
            }
        session["cart"] = cart.items
        session.modified = True

    def total_price(cart):
        return round(
            sum(item["price"] * item["quantity"] for item in cart.items.values()),
            2
        )

#Code adapted from ChatGPT see appendix D
@app.route("/add_to_basket/<int:id>", methods=["POST"])
def add_to_basket(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    qty = request.form.get("quantity", "").strip()
    if not qty:
        quantity = 1
    else:
        quantity = int(qty)

    cur.execute("SELECT id, name, price FROM product WHERE id = %s", (id,))
    prod = cur.fetchone()
    cur.close()
    db.close()

    if not prod:
        return redirect(url_for("search"))

    cart = Cart()
    cart.add(prod["id"], prod["name"], prod["price"], quantity)

    return redirect(url_for("search"))

@app.route("/basket")
def basket():
    cart = Cart()
    items = cart.items.values()
    total = cart.total_price()
    return render_template("basket.html", items=items, total=total)

@app.context_processor
def display_cart_total():
    cart = Cart()
    return {"cart_total": cart.total_price()}

#end of code block for iteration 2 deliverable