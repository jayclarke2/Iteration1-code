#Deliverable: iteration 4
# Version 4.0
#Date: 31/01/2026

#code adapted from existing code and IS3312 Project Phase 2
from flask import render_template
from app import app, get_db
from os import abort

@app.route("/products/<int:id>/details")
def product_detail(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id, name, price, image_url, retailer, category, last_updated FROM product WHERE id = %s""", (id,))
    product = cur.fetchone()

    cur.close()
    db.close()

    if not product:
        abort(404)

    return render_template("product_detail.html", product=product)

#end of code block for iteration 4 deliverable
