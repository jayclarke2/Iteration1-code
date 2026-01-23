#Deliverable: iteration 3
# Version 3.0
#Date: 13/01/2026

#Code source: code below is adapted from existing app.py code from environment and IS3312 project phase 2 - werkzeug module
#Code source: code adapted from youtube video https://www.youtube.com/watch?v=lAY7nXh83fI Create Login and Register Flask App (New) - Complete Tutorial
from flask import render_template, request, redirect, url_for, session, flash
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

        # guest action
        if action == "guest":
            session["guest"] = True
            return redirect(url_for("index"))

        # register action
        if action == "register" and username and password:
            try:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, generate_password_hash(password))
                )
                db.commit()
                flash("Account created successfully! You can now log in.", "success")
            except:
                flash("Username already exists. Please choose another.", "error")

            cur.close(); db.close()
            return redirect(url_for("login"))

        # login action
        if action == "login":
            cur.execute("SELECT id, username, password_hash FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session.update(user_id=user["id"], username=user["username"])
                cur.close(); db.close()
                flash("Logged in successfully!", "success")
                return redirect(url_for("index"))
            else:
                flash("Incorrect username or password.", "error")

            cur.close(); db.close()
            return redirect(url_for("login"))

    cur.close(); db.close()
    return render_template("login.html")

# logout action
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

#end of code block for iteration 3 deliverable