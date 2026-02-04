#Deliverable: iteration 4
# Version 4.0
#Date: 31/01/2026
#
#code below adapted from IS3312 Project Phase 2
#code adapted from IS3312 Project Phase 2 - cart.py

from flask import session, redirect, url_for, render_template, request, flash
from app import app, get_db
from savings import basket_savings_summary, split_store_best_total

class Cart:
    def __init__(self, key="cart"):
        self.key = key
        self.items = session.get(key, {})

    def add(self, prod_id, name, price, retailer=None, region=None, quantity=1):
        pid = str(prod_id)

        if pid in self.items:
            self.items[pid]["quantity"] += quantity
        else:
            self.items[pid] = {
                "id": int(prod_id),
                "name": name,
                "price": float(price),
                "quantity": quantity,
                "retailer": retailer,
                "region": region
            }

        session[self.key] = self.items
        session.modified = True

    def total_price(self):
        return round(sum(i["price"] * i["quantity"] for i in self.items.values()), 2)

# checks if user has picked compare baskets
def choose_basket():
    if session.get("compare_mode"):
        return request.form.get("basket", "1")
    return "single"

# decides products being added to basket 1 or 2
def cart_session(basket_code: str):
    return {"1": "cart_1", "2": "cart_2"}.get(basket_code, "cart")

# locks compare baskets to specific store and region
def lock_keys(basket_code: str):
    if basket_code == "1":
        return "basket_1_retailer", "basket_1_region"
    if basket_code == "2":
        return "basket_2_retailer", "basket_2_region"
    return "basket_retailer", "basket_region"

#Code adapted from ChatGPT see appendix D - Iteration 2 Report
@app.route("/add_to_basket/<int:id>", methods=["POST"])
def add_to_basket(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    qty = request.form.get("quantity", "").strip()
    if not qty:
        quantity = 1
    else:
        quantity = int(qty)

    cur.execute("SELECT id, name, price, retailer, region FROM product WHERE id = %s", (id,))
    product = cur.fetchone()

    cur.close()
    db.close()

    # if compare basket is chosen, adds products to basket 1 and 2 and locks to region and retailer
    if session.get("compare_mode"):
        basket = request.form.get("basket", "1")
        cart_key = "cart_2" if basket == "2" else "cart_1"
        lock_retailer_key = f"basket_{basket}_retailer"
        lock_region_key = f"basket_{basket}_region"
    else:
        cart_key = "cart"
        lock_retailer_key = "basket_retailer"
        lock_region_key = "basket_region"

    # code below added to only allow to build baskets from one retailer/regional store to prevent crossover of products
    locked_retailer = session.get(lock_retailer_key)
    locked_region = session.get(lock_region_key)

    if not locked_retailer and not locked_region:
        session[lock_retailer_key] = product.get("retailer")
        session[lock_region_key] = product.get("region")
    else:
        if locked_retailer != product.get("retailer") or locked_region != product.get("region"):
            flash("You can only add items from the same store to this basket. Clear that basket to switch store.", "danger")
            return redirect(url_for("search"))

    Cart(key=cart_key).add(prod_id=product["id"], name=product["name"], price=product["price"], retailer=product.get("retailer"), region=product.get("region"), quantity=quantity)

    flash("Added to basket", "success")
    return redirect(request.referrer or url_for("search"))

# clear basket
@app.route("/clear_basket", methods=["POST"])
def clear_basket():
    session.pop("cart", None)
    session.pop("basket_retailer", None)
    session.pop("basket_region", None)
    flash("Basket cleared", "info")
    return redirect(url_for("basket"))

# remove item from basket
@app.route("/remove_from_basket/<int:product_id>", methods=["POST"])
def remove_from_basket(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("basket"))

# budget code below is aided from ChatGPT - see appendix C - iteration 3 report
@app.route("/set_budget", methods=["POST"])
def set_budget():
    val = (request.form.get("budget") or "").strip()

    if val == "":
        session.pop("budget_limit", None)
        return redirect(url_for("basket"))

    try:
        budget = float(val)
        if budget <= 0:
            raise ValueError
        session["budget_limit"] = round(budget, 2)
    except ValueError:
        pass

    return redirect(url_for("basket"))


# user story 14 - code aided and adapted through ChatGPT see appendix B - iteration 3 report
fee_rules = {"Supervalu": {"delivery_fee": 4.99, "minimum_spend": 50.00},
    "Aldi": {"delivery_fee": 4.50, "service_fee": 0.35, "bag_fee": 0.25, "minimum_spend": 25.00},
    "Dunnes": {"delivery_fee": 5.49, "minimum_spend": 40.00},
}


@app.route("/basket")
def basket():
    cart = Cart(key="cart")
    items = cart.items.values()
    subtotal = cart.total_price()

    retailer = session.get("basket_retailer")
    rules = fee_rules.get(retailer, {"delivery_fee": 0.00, "service_fee": 0.00, "bag_fee": 0.00})

    # fees
    delivery_fee = float(rules.get("delivery_fee", 0.0) or 0.0)
    service_fee = float(rules.get("service_fee", 0.0) or 0.0)
    bag_fee = float(rules.get("bag_fee", 0.0) or 0.0)
    minimum_spend = rules.get("minimum_spend")

    # total
    fees_total = round(delivery_fee + service_fee + bag_fee, 2)
    grand_total = round(subtotal + fees_total, 2)

    # savings
    savings = basket_savings_summary(list(items), retailer)
    # split store savings
    split_best = split_store_best_total(list(items))

    # user story 19 - split store threshold
    threshold_percent = 0.25
    split_saving = 0.0
    worth_split = False

    if split_best and split_best.get("missing", 0) == 0 and savings and savings.get("current_total"):
        split_saving = round(savings["current_total"] - split_best["total"], 2)

        # worth it if saving is > 25%
        worth_split = split_saving >= (savings["current_total"] * threshold_percent)

    # calculate over budget
    budget_limit = session.get("budget_limit")
    over_by = None
    if budget_limit is not None and float(subtotal) > float(budget_limit):
        over_by = round(float(subtotal) - float(budget_limit), 2)

    return render_template("basket.html", items=items, subtotal=subtotal, delivery_fee=delivery_fee, service_fee=service_fee, bag_fee=bag_fee, fees_total=fees_total, grand_total=grand_total, minimum_spend=minimum_spend, budget_limit=budget_limit, over_by=over_by, savings=savings, split_best=split_best, split_saving=split_saving, worth_split=worth_split)
@app.context_processor
def display_cart_total():
    return {"cart_total": Cart(key="cart").total_price()}

# end of code block for iteration 4 deliverable
