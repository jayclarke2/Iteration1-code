#Deliverable: iteration 3
# Version 3.0
#Date: 20/01/2026
# user story 11 - promotions, discounts, offers
#code adapted from existing app.routes

from app import app, get_db, render_template

# new database table to store deals for specific products - displayed on respective html files
@app.route("/promotions")
def promotions():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT p.name, p.price, p.image_url, p.retailer, d.title, d.deal_price FROM deals d JOIN product p ON p.id = d.product_id WHERE d.deal_type = 'promotion' AND d.is_active = 1 ORDER BY d.id DESC LIMIT 100""")
    products = cur.fetchall()

    cur.close()
    db.close()
    return render_template("promotions.html", products=products)

@app.route("/offers")
def offers():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT p.name, p.price, p.image_url, p.retailer, d.title, d.deal_price FROM deals d JOIN product p ON p.id = d.product_id WHERE d.deal_type = 'offer' AND d.is_active = 1 LIMIT 200""")
    products = cur.fetchall()

    cur.close()
    db.close()
    return render_template("offers.html", products=products)

@app.route("/discounts")
def discounts():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""SELECT p.name, p.price, p.image_url, p.retailer, d.title, d.deal_price FROM deals d JOIN product p ON p.id = d.product_id WHERE d.deal_type = 'discount' AND d.is_active = 1 ORDER BY d.id DESC LIMIT 200""")
    products = cur.fetchall()

    cur.close()
    db.close()
    return render_template("discounts.html", products=products)

# end of code block for iteration 3 deliverable
