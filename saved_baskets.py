# Deliverable: iteration 4
# Version 4.0
# Date 01/02/2026

# Code below aided from ChatGPT see appendix A - Iteration 4 Report

from flask import render_template, request, redirect, url_for, session, flash
from app import app, get_db

# Guests cannot save or load baskets
def require_login():
    return session.get("user_id") is not None and session.get("username") is not None

def cart_is_empty():
    return not session.get("cart")

def set_session_cart_from_rows(rows, retailer, region):
    new_cart = {}
    for row in rows:
        pid = str(row["product_id"])
        new_cart[pid] = {
            "id": int(row["product_id"]),
            "name": row.get("name"),
            "price": float(row.get("price", 0)),
            "quantity": int(row.get("quantity", 1)),
            "retailer": row.get("retailer"),
            "region": row.get("region"),
        }

    session["cart"] = new_cart
    session["basket_retailer"] = retailer
    session["basket_region"] = region
    session.modified = True

@app.route("/saved_baskets")
def saved_baskets():
    if not require_login():
        flash("Log in to save and load baskets.", "error")
        return redirect(url_for("saved_baskets"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT id, name, created_at, retailer, region FROM saved_baskets WHERE user_id = %s ORDER BY created_at DESC""", (session["user_id"],))

    baskets = cur.fetchall()
    cur.close()
    db.close()

    return render_template("saved_baskets.html", baskets=baskets)


@app.route("/save_basket", methods=["POST"])
def save_basket():
    if not require_login():
        flash("Log in to save baskets.", "error")
        return redirect(url_for("login"))

    basket_name = (request.form.get("basket_name") or "").strip()
    if not basket_name:
        basket_name = "My Basket"

    cart = session.get("cart", {})
    if not cart:
        flash("Your basket is empty.", "error")
        return redirect(url_for("basket"))


    items = []
    for pid_str, item in cart.items():
        items.append({
            "product_id": int(pid_str),
            "name": item.get("name"),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 1)),
            "retailer": item.get("retailer"),
            "region": item.get("region"),
        })

    # lock to store retailer and region
    retailer = session.get("basket_retailer")
    region = session.get("basket_region")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # create basket header
    cur.execute("""INSERT INTO saved_baskets (user_id, name, retailer, region) VALUES (%s, %s, %s, %s) """, (session["user_id"], basket_name, retailer, region))
    db.commit()

    basket_id = cur.lastrowid

    # insert items to db table
    cur.executemany(""" INSERT INTO saved_basket_items (basket_id, product_id, name, price, quantity, retailer, region) VALUES (%s, %s, %s, %s, %s, %s, %s) """, [
        (basket_id, i["product_id"], i["name"], i["price"], i["quantity"], i["retailer"], i["region"])
        for i in items
    ])
    db.commit()

    cur.close()
    db.close()

    flash(f"Saved basket: {basket_name}", "success")
    return redirect(url_for("saved_baskets"))

@app.route("/load_basket/<int:basket_id>", methods=["POST"])
def load_basket(basket_id):
    if not require_login():
        flash("Log in to load baskets.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ensure basket belongs to correct user
    cur.execute("""SELECT id, retailer, region FROM saved_baskets WHERE id = %s AND user_id = %s""", (basket_id, session["user_id"]))
    basket = cur.fetchone()

    if not basket:
        cur.close()
        db.close()
        flash("Basket not found.", "error")
        return redirect(url_for("saved_baskets"))

    # Load items from saved basket
    cur.execute("""SELECT product_id, name, price, quantity, retailer, region FROM saved_basket_items WHERE basket_id = %s ORDER BY id ASC""", (basket_id,))
    items = cur.fetchall()

    cur.close()
    db.close()

    # get current basket in session
    current_cart = session.get("cart", {})
    current_retailer = session.get("basket_retailer")
    current_region = session.get("basket_region")

    saved_retailer = basket.get("retailer")
    saved_region = basket.get("region")

    # if there is already a locked store, only allow products to be added if it matches
    if current_cart and (current_retailer or current_region):
        if current_retailer != saved_retailer or current_region != saved_region:
            flash("Cannot load this saved basket because it is from a different store, clear your current basket first.","error")
            return redirect(url_for("saved_baskets"))

    # add items into current cart
    for row in items:
        pid = str(row["product_id"])

        incoming_qty = int(row.get("quantity", 1))
        incoming_item = {
            "id": int(row["product_id"]),
            "name": row.get("name"),
            "price": float(row.get("price", 0)),
            "quantity": incoming_qty,
            "retailer": row.get("retailer"),
            "region": row.get("region"),
        }

        if pid in current_cart:
            # add quantities
            current_cart[pid]["quantity"] = int(current_cart[pid].get("quantity", 1)) + incoming_qty
        else:
            current_cart[pid] = incoming_item

    session["cart"] = current_cart

    # if the basket was empty before, set lock store from saved basket
    if not current_retailer and not current_region:
        session["basket_retailer"] = saved_retailer
        session["basket_region"] = saved_region

    session.modified = True

    flash("Saved basket items added to your current basket.", "success")
    return redirect(url_for("basket"))

@app.route("/delete_saved_basket/<int:basket_id>", methods=["POST"])
def delete_saved_basket(basket_id):
    if not require_login():
        flash("Log in to manage baskets.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ensure user is logged and deleted basket from that user
    cur.execute("""DELETE FROM saved_baskets WHERE id = %s AND user_id = %s """, (basket_id, session["user_id"]))
    db.commit()

    cur.close()
    db.close()

    flash("Saved basket deleted.", "info")
    return redirect(url_for("saved_baskets"))

# user story 23 - use basket template - code adapted from user story 22 code
@app.route("/templates")
def templates():
    if not require_login():
        flash("Log in to use templates.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT id, name, created_at, retailer, region FROM basket_templates WHERE user_id = %s ORDER BY created_at DESC""", (session["user_id"],))
    templates = cur.fetchall()

    cur.close()
    db.close()

    return render_template("templates.html", templates=templates)


@app.route("/save_template", methods=["POST"])
def save_template():
    if not require_login():
        flash("Log in to save templates.", "error")
        return redirect(url_for("login"))

    template_name = (request.form.get("template_name") or "").strip() or "My Template"

    cart = session.get("cart", {})
    if not cart:
        flash("Your basket is empty. Cannot create template", "error")
        return redirect(url_for("basket"))

    retailer = session.get("basket_retailer")
    region = session.get("basket_region")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        INSERT INTO basket_templates (user_id, name, retailer, region) VALUES (%s, %s, %s, %s)""", (session["user_id"], template_name, retailer, region))
    db.commit()
    template_id = cur.lastrowid

    rows = []
    for pid_str, item in cart.items():
        rows.append((
            template_id,
            int(item.get("id") or pid_str),
            item.get("name"),
            float(item.get("price", 0)),
            int(item.get("quantity", 1)),
            item.get("retailer"),
            item.get("region"),
        ))

    cur.executemany("""INSERT INTO basket_template_items (template_id, product_id, name, price, quantity, retailer, region) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, rows)
    db.commit()

    cur.close()
    db.close()

    flash(f"Template saved: {template_name}", "success")
    return redirect(url_for("templates"))


@app.route("/start_from_template/<int:template_id>", methods=["POST"])
def start_from_template(template_id):
    if not require_login():
        flash("Log in to use templates.", "error")
        return redirect(url_for("login"))

    if not cart_is_empty():
        flash("Clear your basket before starting from a template.", "error")
        return redirect(url_for("basket"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # ownership check
    cur.execute("""
        SELECT id, retailer, region FROM basket_templates WHERE id = %s AND user_id = %s""", (template_id, session["user_id"]))
    template = cur.fetchone()

    if not template:
        cur.close()
        db.close()
        flash("Template not found.", "error")
        return redirect(url_for("templates"))

    cur.execute("""
        SELECT product_id, name, price, quantity, retailer, region FROM basket_template_items WHERE template_id = %s ORDER BY id ASC""", (template_id,))
    items = cur.fetchall()

    cur.close()
    db.close()

    set_session_cart_from_rows(items, template.get("retailer"), template.get("region"))
    flash("Started basket from template.", "success")
    return redirect(url_for("basket"))


@app.route("/delete_template/<int:template_id>", methods=["POST"])
def delete_template(template_id):
    if not require_login():
        flash("Log in to manage templates.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""DELETE FROM basket_templates WHERE id = %s AND user_id = %s""", (template_id, session["user_id"]))
    db.commit()

    cur.close()
    db.close()

    flash("Template deleted.", "info")
    return redirect(url_for("templates"))

# end of code block for iteration 4 deliverable