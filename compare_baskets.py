#Deliverable: iteration 3
# Version 3.0
#Date: 16/01/2026

# code below adapted from existing basket.py code to create two seperate baskets

from app import app
from flask import session, redirect, url_for, render_template, request

@app.route("/set_compare_mode", methods=["POST"])
def set_compare_mode():
    session["compare_mode"] = (request.form.get("mode") == "compare")
    return redirect(url_for("search"))

@app.route("/clear_compare_baskets", methods=["POST"])
def clear_compare_baskets():
    session.pop("cart_1", None)
    session.pop("cart_2", None)
    session.pop("basket_1_retailer", None)
    session.pop("basket_1_region", None)
    session.pop("basket_2_retailer", None)
    session.pop("basket_2_region", None)
    return redirect(url_for("compare_baskets"))

@app.route("/compare_baskets")
def compare_baskets():
    cart_1 = session.get("cart_1", {})
    cart_2 = session.get("cart_2", {})

    items_1 = list(cart_1.values())
    items_2 = list(cart_2.values())

    subtotal_1 = round(sum(i["price"] * i["quantity"] for i in items_1), 2)
    subtotal_2 = round(sum(i["price"] * i["quantity"] for i in items_2), 2)

    diff = round(subtotal_1 - subtotal_2, 2)

    return render_template("compare_baskets.html", items_1=items_1, items_2=items_2, subtotal_1=subtotal_1, subtotal_2=subtotal_2, diff=diff, basket_1_retailer=session.get("basket_1_retailer"), basket_1_region=session.get("basket_1_region"), basket_2_retailer=session.get("basket_2_retailer"), basket_2_region=session.get("basket_2_region"),)

# end of code block for iteration 3 deliverable