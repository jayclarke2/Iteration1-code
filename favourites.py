#Deliverable: iteration 4
# Version 4.0
#Date: 02/02/2026

#code aided from ChatGPT - see appendix B - iteration 4 report

from flask import render_template, request, redirect, url_for, session, flash
from app import app, get_db

def require_login():
    return session.get("user_id") is not None and session.get("username") is not None and not session.get("guest")

@app.route("/favourites")
def favourites():
    if not require_login():
        flash("Log in to use favourites.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT p.id, p.name, p.price, p.member_price, p.retailer, p.region, p.image_url FROM favourites f JOIN product p ON p.id = f.product_id WHERE f.user_id = %s ORDER BY f.created_at DESC""", (session["user_id"],))
    products = cur.fetchall()

    cur.close(); db.close()
    return render_template("favourites.html", products=products)

@app.route("/favourite/<int:product_id>", methods=["POST"])
def favourite(product_id):
    if not require_login():
        flash("Log in to favourite items.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Insert or ignore duplicates
    cur.execute("""INSERT INTO favourites (user_id, product_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE created_at = created_at""", (session["user_id"], product_id))
    db.commit()

    cur.close(); db.close()
    flash("Added to favourites.", "success")
    return redirect(request.referrer or url_for("search"))

@app.route("/unfavourite/<int:product_id>", methods=["POST"])
def unfavourite(product_id):
    if not require_login():
        flash("Log in to manage favourites.", "error")
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("DELETE FROM favourites WHERE user_id=%s AND product_id=%s",
                (session["user_id"], product_id))
    db.commit()

    cur.close(); db.close()
    flash("Removed from favourites.", "info")
    return redirect(request.referrer or url_for("favourites"))

# end of code block for iteration 4 deliverable