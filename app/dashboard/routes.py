from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from ..models import db, Account, Transaction


dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard.route("/")
@login_required
def index():

    # --------------------------------------------------
    # TOTAL INCOME
    # --------------------------------------------------

    total_income = (
        db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0
            )
        )
        .filter(
            Transaction.transaction_type == "income"
        )
        .scalar()
    )

    income_count = (
        Transaction.query
        .filter(
            Transaction.transaction_type == "income"
        )
        .count()
    )

    # --------------------------------------------------
    # TOTAL EXPENSE
    # --------------------------------------------------

    total_expense = (
        db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0
            )
        )
        .filter(
            Transaction.transaction_type == "expense"
        )
        .scalar()
    )

    expense_count = (
        Transaction.query
        .filter(
            Transaction.transaction_type == "expense"
        )
        .count()
    )

    # --------------------------------------------------
    # TRANSACTION COUNT
    # --------------------------------------------------

    transaction_count = Transaction.query.count()

    # --------------------------------------------------
    # NET BALANCE
    # --------------------------------------------------

    total_income = Decimal(str(total_income or 0))
    total_expense = Decimal(str(total_expense or 0))

    net_balance = total_income - total_expense

    # --------------------------------------------------
    # RECENT TRANSACTIONS
    # --------------------------------------------------

    recent_transactions = (
        Transaction.query
        .order_by(
            Transaction.transaction_date.desc()
        )
        .limit(10)
        .all()
    )

    # --------------------------------------------------
    # ACTIVE ACCOUNTS
    # --------------------------------------------------

    accounts = (
        Account.query
        .filter(
            Account.status == "active"
        )
        .order_by(
            Account.created_at.desc()
        )
        .all()
    )

    # --------------------------------------------------
    # TOTAL ACCOUNT BALANCE
    # --------------------------------------------------

    total_account_balance = (
        db.session.query(
            func.coalesce(
                func.sum(Account.current_balance),
                0
            )
        )
        .filter(
            Account.status == "active"
        )
        .scalar()
    )

    total_account_balance = Decimal(
        str(total_account_balance or 0)
    )

    # --------------------------------------------------
    # RENDER DASHBOARD
    # --------------------------------------------------

    return render_template(
        "dashboard/index.html",
        total_income=total_income,
        income_count=income_count,
        total_expense=total_expense,
        expense_count=expense_count,
        net_balance=net_balance,
        transaction_count=transaction_count,
        recent_transactions=recent_transactions,
        accounts=accounts,
        total_account_balance=total_account_balance
    )