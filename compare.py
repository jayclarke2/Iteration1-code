#Deliverable: iteration 2
# Version 2.0
#Date: 16/11/2025

#code adapted from existing code in search.py
from flask import request, render_template
from app import app, get_db

@app.route("/compare")
def compare():
    db = get_db()
    cur = db.cursor(dictionary=True)

    compare_query = request.args.get("compare")
    compare_results = []

    if compare_query:
        cur.execute("""
            SELECT retailer, ANY_VALUE(name) AS name, MIN(price) AS price, ANY_VALUE(region) AS region FROM product WHERE name LIKE %s GROUP BY retailer ORDER BY price ASC
        """, ("%" + compare_query + "%",))

        compare_results = cur.fetchall()

        cur.close()
        db.close()

    return render_template("index.html", compare_results=compare_results, compare_query=compare_query)

#end of code block for iteration 2 deliverable