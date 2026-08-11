from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func

from ..models import db, Account

accounts = Blueprint("accounts", "app.accounts.routes", url_prefix="/accounts")


def parse_balance(value):
    try:
        amount = Decimal(str(value or "0").replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None

    if amount < Decimal("0"):
        return None

    return amount.quantize(Decimal("0.01"))


@accounts.route("/")
@login_required
def index():
    accounts_list = Account.query.order_by(Account.created_at.desc()).all()

    cash_total = db.session.query(
        func.coalesce(func.sum(Account.current_balance), 0)
    ).filter(
        Account.account_type == "cash",
        Account.status == "active"
    ).scalar()

    bank_total = db.session.query(
        func.coalesce(func.sum(Account.current_balance), 0)
    ).filter(
        Account.account_type == "bank",
        Account.status == "active"
    ).scalar()

    mobile_money_total = db.session.query(
        func.coalesce(func.sum(Account.current_balance), 0)
    ).filter(
        Account.account_type == "mobile_money",
        Account.status == "active"
    ).scalar()

    return render_template(
        "accounts/index.html",
        accounts=accounts_list,
        cash_total=cash_total,
        bank_total=bank_total,
        mobile_money_total=mobile_money_total
    )


@accounts.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        account_type = request.form.get("account_type", "").strip().lower()
        account_number = request.form.get("account_number", "").strip()
        opening_balance_input = request.form.get("opening_balance", "0").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Account name is required.", "danger")
            return render_template("accounts/add.html")

        if account_type not in {"cash", "bank", "mobile_money"}:
            flash("Invalid account type.", "danger")
            return render_template("accounts/add.html")

        opening_balance = parse_balance(opening_balance_input)

        if opening_balance is None:
            flash(
                "Opening balance must be a valid non-negative number.",
                "danger"
            )
            return render_template("accounts/add.html")

        if account_number:
            existing_account = Account.query.filter(
                Account.account_number == account_number
            ).first()

            if existing_account:
                flash("Account number already exists.", "danger")
                return render_template("accounts/add.html")

        account = Account(
            name=name,
            account_type=account_type,
            account_number=account_number or None,
            opening_balance=opening_balance,
            current_balance=opening_balance,
            description=description or None,
            status="active"
        )

        try:
            db.session.add(account)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Account could not be created.", "danger")
            return render_template("accounts/add.html")

        flash(
            f"Account '{name}' created successfully.",
            "success"
        )

        return redirect(url_for("accounts.index"))

    return render_template("accounts/add.html")


@accounts.route("/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def edit(account_id):
    account = db.session.get(Account, account_id)

    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        account_type = request.form.get("account_type", "").strip().lower()
        account_number = request.form.get("account_number", "").strip()
        opening_balance_input = request.form.get(
            "opening_balance",
            "0"
        ).strip()
        current_balance_input = request.form.get(
            "current_balance",
            "0"
        ).strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active").strip().lower()

        if not name:
            flash("Account name is required.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        if account_type not in {"cash", "bank", "mobile_money"}:
            flash("Invalid account type.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        if status not in {"active", "inactive"}:
            flash("Invalid account status.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        opening_balance = parse_balance(opening_balance_input)
        current_balance = parse_balance(current_balance_input)

        if opening_balance is None:
            flash("Opening balance must be valid.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        if current_balance is None:
            flash("Current balance must be valid.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        if account_number:
            duplicate = Account.query.filter(
                Account.account_number == account_number,
                Account.id != account.id
            ).first()

            if duplicate:
                flash(
                    "Account number already exists.",
                    "danger"
                )
                return render_template(
                    "accounts/edit.html",
                    account=account
                )

        account.name = name
        account.account_type = account_type
        account.account_number = account_number or None
        account.opening_balance = opening_balance
        account.current_balance = current_balance
        account.description = description or None
        account.status = status

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Account could not be updated.", "danger")
            return render_template(
                "accounts/edit.html",
                account=account
            )

        flash(
            f"Account '{account.name}' updated successfully.",
            "success"
        )

        return redirect(url_for("accounts.index"))

    return render_template(
        "accounts/edit.html",
        account=account
    )


@accounts.route("/<int:account_id>")
@login_required
def detail(account_id):
    account = db.session.get(Account, account_id)

    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))

    return render_template(
        "accounts/detail.html",
        account=account
    )


@accounts.route(
    "/<int:account_id>/deactivate",
    methods=["POST"]
)
@login_required
def deactivate(account_id):
    account = db.session.get(Account, account_id)

    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))

    account.status = "inactive"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Account could not be deactivated.",
            "danger"
        )
        return redirect(url_for("accounts.index"))

    flash(
        f"Account '{account.name}' has been deactivated.",
        "success"
    )

    return redirect(url_for("accounts.index"))


@accounts.route(
    "/<int:account_id>/activate",
    methods=["POST"]
)
@login_required
def activate(account_id):
    account = db.session.get(Account, account_id)

    if not account:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))

    account.status = "active"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Account could not be activated.",
            "danger"
        )
        return redirect(url_for("accounts.index"))

    flash(
        f"Account '{account.name}' has been activated.",
        "success"
    )

    return redirect(url_for("accounts.index"))