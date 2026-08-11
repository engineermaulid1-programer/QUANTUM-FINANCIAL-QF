from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from ..models import User


auth = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(username=username).first()

        if user is None:
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Your account is inactive. Contact the administrator.", "warning")
            return render_template("auth/login.html")

        if not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        login_user(user)

        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth.route("/logout")
def logout():

    logout_user()

    return redirect(url_for("auth.login"))