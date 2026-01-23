#Deliverable: iteration 3
# Version 3.0
#Date: 13/01/2026

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
            SELECT id, name, price, retailer, region FROM product WHERE name LIKE %s ORDER BY retailer, price ASC
        """, ("%" + compare_query + "%",))

        rows = cur.fetchall()
        compare_results = []
        seen = set()

        for r in rows:
            if r["retailer"] not in seen:
                compare_results.append(r)
                seen.add(r["retailer"])

        cur.close()
        db.close()

    return render_template("index.html", compare_results=compare_results, compare_query=compare_query)

#end of code block for iteration 3 deliverable