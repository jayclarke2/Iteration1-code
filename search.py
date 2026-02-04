#Deliverable: iteration 4
# Version 4.0
#Date: 31/01/2026

#Code source: code adapted from existing code for connection to database and sql command
#code adapted from ChatGPT 4o see appendix B - Iteration 2 report
#Code source: code adapted from Master flask API in 10 minutes - https://www.youtube.com/watch?v=h3PX_NaeazA
#code source: from youtube video Pagination in Flask: Split Your Data Into Pages - https://www.youtube.com/watch?v=U18hO1ngZEQ

from flask import render_template, request, session, redirect,url_for
from app import app, get_db
from unit import unit_price

# user story 21 select preferred retailer/store
@app.route("/preferred_region", methods=["POST"])
def preferred_region():
    session["preferred_region"] = request.form.get("region", "")
    return redirect(url_for("search"))
# Search page getting query request
@app.route("/search", methods=["GET"])
def search():
    db = get_db()
    cur = db.cursor(dictionary=True)

    # user story 21 - choose preferred store/retailer - code adapted to save preference
    query = (request.args.get("query") or "").strip()
    selected_retailer = request.args.get("retailer")
    preferred_region = session.get("preferred_region", "")
    selected_region = (request.args.get("region") if "region" in request.args else preferred_region) or ""
    selected_category = request.args.get("category")
    sort = request.args.get("sort") or ""
    rows = []

    sql = """SELECT id, name, price, member_price, retailer, category, image_url, last_updated, region FROM product WHERE 1=1"""
    params = []

    if query:
        sql += " AND name LIKE %s"
        params.append("%" + query + "%")

    if selected_retailer not in (None, ""):
        sql += " AND retailer = %s"
        params.append(selected_retailer)

    if selected_category not in (None, ""):
        sql += " AND category = %s"
        params.append(selected_category)

    if selected_region:
        sql += " AND region = %s"
        params.append(selected_region)

    if sort == "price_asc":
        sql += " ORDER BY price ASC"
    elif sort == "price_desc":
        sql += " ORDER BY price DESC"

    cur.execute(sql, params)
    rows = cur.fetchall()

    # select retailer and category and region
    cur.execute("SELECT DISTINCT retailer FROM product ORDER BY retailer")
    retailers = [row["retailer"] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT category FROM product ORDER BY category")
    categories = [row["category"] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT region FROM product ORDER BY region")
    regions = [row["region"] for row in cur.fetchall()]

    cur.close()
    db.close()

    # Calculate unit price
    for row in rows:
        unit_price(row)

    # Unit price sorting - Code aided with ChatGPT see appendix B:
    if sort == "unit_asc":
        rows_with_unit = [r for r in rows if r.get("unit_price") is not None]
        rows_without_unit = [r for r in rows if r.get("unit_price") is None]
        rows_with_unit.sort(key=lambda r: r["unit_price"])
        rows = rows_with_unit + rows_without_unit

    elif sort == "unit_desc":
        rows_with_unit = [r for r in rows if r.get("unit_price") is not None]
        rows_without_unit = [r for r in rows if r.get("unit_price") is None]
        rows_with_unit.sort(key=lambda r: r["unit_price"], reverse=True)
        rows = rows_with_unit + rows_without_unit

    #code adapted from youtube video Pagination in Flask: Split Your Data Into Pages - https://www.youtube.com/watch?v=U18hO1ngZEQ
    page = request.args.get("page", 1, type=int)
    per_page = 40

    total = len(rows)
    pages = (total // per_page) + (1 if total % per_page else 0)

    start = (page - 1) * per_page
    end = start + per_page
    rows = rows[start:end]

    return render_template("search.html", query=query, rows=rows, retailers=retailers, categories=categories, regions=regions, selected_region=selected_region, selected_retailer=selected_retailer, selected_category=selected_category, sort=sort, page=page, pages=pages)

# end of code block for iteration 4 deliverable