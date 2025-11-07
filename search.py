#Deliverable: iteration 1
# Version 1.0
#Date: 02/11/2025

#Code source: code adapted from existing code for connection to database and sql command
#Code source: code adapted from ChatGPT 4o see appendix B
from flask import render_template, request
from app import app, get_db
from unit import unit_price


# Search page getting query request
@app.route("/search", methods=["GET"])
def search():
    query = (request.args.get("query") or "").strip()
    rows = []
    if query:
        like = "%" + query + "%"
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT name, price, image_url, last_updated FROM product WHERE name LIKE %s ORDER BY name DESC",
            (like,)
        )
        rows = cur.fetchall()
        cur.close()
        db.close()
        for row in rows:
            unit_price(row)

    return render_template("search.html", query=query, rows=rows,)

#end of code block for iteration 1 deliverable
