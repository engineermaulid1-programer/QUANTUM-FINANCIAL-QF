from datetime import date
from calendar import month_name

from flask import Blueprint, render_template, request
from flask_login import login_required

from ..models import Transaction, Account


reports = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@reports.route("/")
@login_required
def index():

    # =========================================================
    # REPORT FILTERS
    # =========================================================

    selected_year = request.args.get(
        "year",
        ""
    ).strip()

    custom_year = request.args.get(
        "custom_year",
        ""
    ).strip()

    selected_month = request.args.get(
        "month",
        ""
    ).strip()


    # =========================================================
    # AVAILABLE YEARS
    # =========================================================

    available_years = sorted(
        {
            transaction.transaction_date.year
            for transaction in Transaction.query.all()
            if transaction.transaction_date
        },
        reverse=True
    )


    # =========================================================
    # MONTHS
    # =========================================================

    months = [
        (month, month_name[month])
        for month in range(1, 13)
    ]


    # =========================================================
    # DETERMINE YEAR
    # =========================================================

    selected_year_value = None

    # Manual year has priority
    if custom_year:

        try:
            manual_year = int(custom_year)

            if 1900 <= manual_year <= 2100:
                selected_year_value = manual_year

        except ValueError:
            custom_year = ""


    # If no manual year, use dropdown year
    if selected_year_value is None and selected_year:

        try:
            selected_year_value = int(selected_year)

        except ValueError:
            selected_year = ""


    # =========================================================
    # DETERMINE MONTH
    # =========================================================

    selected_month_value = None

    if selected_month:

        try:
            month_number = int(selected_month)

            if 1 <= month_number <= 12:
                selected_month_value = month_number

        except ValueError:
            selected_month = ""


    # =========================================================
    # TRANSACTION QUERY
    # =========================================================

    query = Transaction.query


    # YEAR FILTER
    if selected_year_value:

        start_date = date(
            selected_year_value,
            1,
            1
        )

        end_date = date(
            selected_year_value,
            12,
            31
        )

        query = query.filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )


    # MONTH FILTER
    if selected_month_value:

        if selected_year_value:

            month_start = date(
                selected_year_value,
                selected_month_value,
                1
            )

            if selected_month_value == 12:

                month_end = date(
                    selected_year_value,
                    12,
                    31
                )

            else:

                next_month = date(
                    selected_year_value,
                    selected_month_value + 1,
                    1
                )

                month_end = next_month.fromordinal(
                    next_month.toordinal() - 1
                )

            query = query.filter(
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end
            )


        else:

            # Month-only filtering when no year is selected
            transactions_for_month = query.all()

            transactions_for_month = [
                transaction
                for transaction in transactions_for_month
                if (
                    transaction.transaction_date
                    and
                    transaction.transaction_date.month
                    == selected_month_value
                )
            ]

            transactions = transactions_for_month

            query = None


    # =========================================================
    # GET TRANSACTIONS
    # =========================================================

    if query is not None:

        transactions = (
            query
            .order_by(
                Transaction.transaction_date.desc(),
                Transaction.id.desc()
            )
            .all()
        )


    # =========================================================
    # TOTAL INCOME
    # =========================================================

    total_income = sum(
        float(transaction.amount)
        for transaction in transactions
        if transaction.transaction_type == "income"
    )


    # =========================================================
    # TOTAL EXPENSE
    # =========================================================

    total_expense = sum(
        float(transaction.amount)
        for transaction in transactions
        if transaction.transaction_type == "expense"
    )


    # =========================================================
    # NET BALANCE
    # =========================================================

    net_balance = (
        total_income
        - total_expense
    )


    # =========================================================
    # TRANSACTION COUNTS
    # =========================================================

    transaction_count = len(transactions)

    income_count = sum(
        1
        for transaction in transactions
        if transaction.transaction_type == "income"
    )

    expense_count = sum(
        1
        for transaction in transactions
        if transaction.transaction_type == "expense"
    )


    # =========================================================
    # CATEGORY SUMMARY
    # =========================================================

    category_data = {}


    for transaction in transactions:

        category = (
            transaction.category
            or "Uncategorized"
        )

        if category not in category_data:

            category_data[category] = {
                "income": 0,
                "expense": 0
            }


        if transaction.transaction_type == "income":

            category_data[category]["income"] += float(
                transaction.amount
            )

        else:

            category_data[category]["expense"] += float(
                transaction.amount
            )


    category_summary = []


    for category, values in category_data.items():

        category_summary.append({
            "category": category,
            "income": values["income"],
            "expense": values["expense"]
        })


    category_summary.sort(
        key=lambda item:
        item["income"] + item["expense"],
        reverse=True
    )


    # =========================================================
    # MONTHLY PERFORMANCE
    # =========================================================

    monthly_data = {}


    for transaction in transactions:

        month_key = transaction.transaction_date.strftime(
            "%Y-%m"
        )

        month_label = transaction.transaction_date.strftime(
            "%B %Y"
        )


        if month_key not in monthly_data:

            monthly_data[month_key] = {
                "month": month_label,
                "income": 0,
                "expense": 0
            }


        if transaction.transaction_type == "income":

            monthly_data[month_key]["income"] += float(
                transaction.amount
            )

        else:

            monthly_data[month_key]["expense"] += float(
                transaction.amount
            )


    monthly_summary = list(
        monthly_data.values()
    )


    monthly_summary.sort(
        key=lambda item: item["month"]
    )


    # =========================================================
    # ACCOUNTS
    # =========================================================

    accounts = (
        Account.query
        .filter_by(status="active")
        .order_by(Account.name.asc())
        .all()
    )


    total_account_balance = sum(
        float(account.current_balance)
        for account in accounts
    )


    # =========================================================
    # RECENT TRANSACTIONS
    # =========================================================

    recent_transactions = transactions[:10]


    # =========================================================
    # REPORT LABEL
    # =========================================================

    if selected_year_value and selected_month_value:

        report_period = (
            f"{month_name[selected_month_value]} "
            f"{selected_year_value}"
        )

    elif selected_year_value:

        report_period = (
            f"Year {selected_year_value}"
        )

    elif selected_month_value:

        report_period = (
            f"All Years — "
            f"{month_name[selected_month_value]}"
        )

    else:

        report_period = "All Transactions"


    # =========================================================
    # RENDER
    # =========================================================

    return render_template(
        "reports/index.html",

        transactions=transactions,
        recent_transactions=recent_transactions,

        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,

        transaction_count=transaction_count,
        income_count=income_count,
        expense_count=expense_count,

        category_summary=category_summary,
        monthly_summary=monthly_summary,

        accounts=accounts,
        total_account_balance=total_account_balance,

        available_years=available_years,
        months=months,

        selected_year=selected_year,
        custom_year=custom_year,
        selected_month=selected_month,

        report_period=report_period
    )