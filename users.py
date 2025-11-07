#Deliverable: iteration 1
# Version 1.0
#Date: 01/11/2025

#Code source: code below is adapted from existing app.py code from environment and IS3312 project phase 2 - werkzeug module
#Code source: code adapted from youtube video https://www.youtube.com/watch?v=lAY7nXh83fI Create Login and Register Flask App (New) - Complete Tutorial
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, get_db

@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if action == "guest":
            session["guest"] = True
            return redirect(url_for("index"))

        if action == "register" and username and password:
            try:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except:
                pass

        if action == "login":
            cur.execute("SELECT id, username, password_hash FROM users WHERE username=%s", (username,))
            username = cur.fetchone()
            if username and check_password_hash(username["password_hash"], password):
                session.clear()
                session.update(user_id=username["id"], username=username["username"])
                cur.close(); db.close()
                return redirect(url_for("index"))

        cur.close(); db.close()
        return redirect(url_for("login"))


    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

#End of code block for iteration 1 deliverable