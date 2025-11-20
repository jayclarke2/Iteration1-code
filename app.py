#Deliverable: iteration 2
# Version 2.0
#Date: 13/11/2025

# Code below is adapted from Python - Connect to MySQL Database with PyCharm - https://www.youtube.com/watch?v=elWvom3F2tQ – used to connect MySQL database with Python
# Code below is adapted from youtube video, Flask CRUD App with MySQL & XAMPP | Simple Backend & Frontend Tutorial – https://www.youtube.com/watch?v=3YKyyskO_fE&t=482s – used to aid code in deleting, editing and adding products

from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector, sys, subprocess

app = Flask(__name__)
app.secret_key = "key-secret"

# Database connector
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="FYP",
        database="fyp_grocery"
    )
# Home page
@app.route("/")
def index():
    if session.get("user_id") or session.get("guest"):
        return render_template("index.html")

    return redirect(url_for("login"))


# Products page (admin)
@app.route("/products", methods=["GET", "POST"])
def products():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        image_url = request.form.get("image_url", "").strip()

        if name and price and image_url:
            cur.execute(
                "INSERT INTO product (name, image_url, price) VALUES (%s, %s, %s)",
                (name, image_url, price)
            )
            db.commit()

    cur.execute("SELECT id, name, last_updated, image_url, price FROM product ORDER BY id ASC")
    products = cur.fetchall()

    cur.close()
    db.close()

    return render_template("products.html", products=products)


# Edit product
@app.route("/products/<int:id>/edit", methods=["GET", "POST"])
def edit_product(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        image_url = request.form.get("image_url", "").strip()

        if name and price and image_url:
            cur.execute(
                "UPDATE product SET name = %s, price = %s, image_url = %s WHERE id = %s",
                (name, price, image_url, id)
            )
            db.commit()
            cur.close()
            db.close()
            return redirect(url_for("products"))

    cur.execute("SELECT id, name, price, image_url, last_updated FROM product WHERE id = %s", (id,))
    product = cur.fetchone()

    cur.close()
    db.close()
    return render_template("edit_product.html", product=product)

# Delete product
@app.route("/products/<int:id>/delete", methods=["POST"])
def delete_product(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM product WHERE id = %s", (id,))
    db.commit()
    cur.close()
    db.close()
    return redirect(url_for("products"))

#code adapted from ChatGPT see appendix A
@app.route("/refresh_prices", methods=["POST"])
def refresh_prices():
    try:
        subprocess.run([sys.executable, "scrape_supervalu.py"], check=True)
        print(" SuperValu data refreshed.")
    except Exception as e:
        print(" Error running scraper:", e)
    return redirect(url_for("products"))

import search
import users
import product_detail
import compare
import basket

if __name__ == "__main__":
    app.run(debug=True)

#end of code block for iteration 2 deliverable