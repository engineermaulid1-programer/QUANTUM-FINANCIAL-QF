from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required

from ..models import db, User
from ..permissions import role_required


users = Blueprint(
    "users",
    __name__,
    url_prefix="/users"
)


@users.route("/")
@role_required("administrator")
def index():

    users_list = (
        User.query
        .order_by(User.created_at.desc())
        .all()
    )

    return render_template(
        "users/index.html",
        users=users_list
    )


@users.route("/add", methods=["GET", "POST"])
@role_required("administrator")
def add():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        role = request.form.get(
            "role",
            "staff"
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------------
        # VALIDATION
        # -------------------------------

        if not full_name:
            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if not username:
            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if User.query.filter_by(
            username=username
        ).first():

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if email:

            existing_email = User.query.filter_by(
                email=email
            ).first()

            if existing_email:

                flash(
                    "Email address already exists.",
                    "danger"
                )

                return render_template(
                    "users/add.html"
                )

        allowed_roles = [
            "administrator",
            "finance_manager",
            "accountant",
            "staff"
        ]

        if role not in allowed_roles:

            flash(
                "Invalid user role.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "users/add.html"
            )

        # -------------------------------
        # CREATE USER
        # -------------------------------

        user = User(
            full_name=full_name,
            username=username,
            email=email or None,
            role=role,
            is_active=True
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            f"User '{username}' created successfully.",
            "success"
        )

        return redirect(
            url_for("users.index")
        )

    return render_template(
        "users/add.html"
    )