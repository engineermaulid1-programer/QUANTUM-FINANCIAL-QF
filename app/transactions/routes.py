import os
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..models import db, Transaction, Account, Receipt


transactions = Blueprint(
    "transactions",
    __name__,
    url_prefix="/transactions"
)


ALLOWED_RECEIPT_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "pdf"
}

MAX_RECEIPT_SIZE = 10 * 1024 * 1024


def get_active_accounts():
    return (
        Account.query
        .filter_by(status="active")
        .order_by(Account.name.asc())
        .all()
    )


def receipt_allowed(filename):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_RECEIPT_EXTENSIONS


def save_receipt_file(file):
    if not file or not file.filename:
        return None

    if not receipt_allowed(file.filename):
        return None

    original_filename = secure_filename(file.filename)

    extension = original_filename.rsplit(".", 1)[1].lower()

    stored_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    receipt_directory = os.path.join(
        current_app.instance_path,
        "receipts"
    )

    os.makedirs(
        receipt_directory,
        exist_ok=True
    )

    file_path = os.path.join(
        receipt_directory,
        stored_filename
    )

    file.save(file_path)

    file_size = os.path.getsize(file_path)

    if file_size > MAX_RECEIPT_SIZE:
        try:
            os.remove(file_path)
        except OSError:
            pass

        raise ValueError(
            "Receipt file must not exceed 10 MB."
        )

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "mime_type": file.mimetype,
        "file_size": file_size
    }


def delete_receipt_file(receipt):
    if not receipt:
        return

    if receipt.file_path:
        try:
            if os.path.exists(receipt.file_path):
                os.remove(receipt.file_path)
        except OSError:
            pass


@transactions.route("/")
@login_required
def index():

    transactions_list = (
        Transaction.query
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc()
        )
        .all()
    )

    total_income = sum(
        (
            Decimal(str(t.amount))
            for t in transactions_list
            if t.transaction_type == "income"
        ),
        Decimal("0.00")
    )

    total_expense = sum(
        (
            Decimal(str(t.amount))
            for t in transactions_list
            if t.transaction_type == "expense"
        ),
        Decimal("0.00")
    )

    net_balance = total_income - total_expense

    return render_template(
        "transactions/index.html",
        transactions=transactions_list,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance
    )


@transactions.route("/add", methods=["GET", "POST"])
@login_required
def add():

    accounts = get_active_accounts()

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        ).strip().lower()

        amount_input = request.form.get(
            "amount",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        transaction_date_input = request.form.get(
            "transaction_date",
            ""
        ).strip()

        account_id_input = request.form.get(
            "account_id",
            ""
        ).strip()

        if transaction_type not in {"income", "expense"}:
            flash(
                "Please select a valid transaction type.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if not amount_input:
            flash(
                "Transaction amount is required.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        try:
            amount = Decimal(amount_input)
        except (InvalidOperation, ValueError):
            flash(
                "Amount must be a valid number.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if amount <= Decimal("0"):
            flash(
                "Transaction amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if not description:
            flash(
                "Description is required.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if not category:
            flash(
                "Category is required.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if not transaction_date_input:
            flash(
                "Transaction date is required.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        try:
            transaction_date = date.fromisoformat(
                transaction_date_input
            )
        except ValueError:
            flash(
                "Invalid transaction date.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if not account_id_input:
            flash(
                "Please select a financial account.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        try:
            account_id = int(account_id_input)
        except (TypeError, ValueError):
            flash(
                "Invalid financial account.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        account = db.session.get(
            Account,
            account_id
        )

        if not account:
            flash(
                "Selected financial account was not found.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        if account.status != "active":
            flash(
                "Selected financial account is not active.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        current_balance = Decimal(
            str(account.current_balance or 0)
        )

        if transaction_type == "expense":

            if amount > current_balance:
                flash(
                    "Insufficient balance in the selected account.",
                    "danger"
                )

                return render_template(
                    "transactions/add.html",
                    accounts=accounts
                )

        transaction = Transaction(
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            category=category,
            transaction_date=transaction_date,
            status="completed",
            created_by=current_user.id,
            account_id=account.id
        )

        db.session.add(transaction)

        if transaction_type == "income":
            account.current_balance = (
                current_balance + amount
            )
        else:
            account.current_balance = (
                current_balance - amount
            )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

            flash(
                "Transaction could not be saved.",
                "danger"
            )

            return render_template(
                "transactions/add.html",
                accounts=accounts
            )

        flash(
            "Transaction added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    return render_template(
        "transactions/add.html",
        accounts=accounts
    )


@transactions.route("/<int:transaction_id>")
@login_required
def detail(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    return render_template(
        "transactions/detail.html",
        transaction=transaction
    )


@transactions.route(
    "/<int:transaction_id>/receipt",
    methods=["POST"]
)
@login_required
def upload_receipt(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    receipt_file = request.files.get(
        "receipt"
    )

    if not receipt_file or not receipt_file.filename:
        flash(
            "Please select a receipt file.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    if not receipt_allowed(receipt_file.filename):
        flash(
            "Invalid receipt format. Use JPG, JPEG, PNG, WEBP or PDF.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    try:
        receipt_data = save_receipt_file(
            receipt_file
        )

    except ValueError as error:
        flash(
            str(error),
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    except Exception:
        flash(
            "Receipt could not be uploaded.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    if not receipt_data:
        flash(
            "Receipt could not be processed.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    old_receipt = transaction.receipt

    if old_receipt:
        delete_receipt_file(old_receipt)

        old_receipt.original_filename = (
            receipt_data["original_filename"]
        )

        old_receipt.stored_filename = (
            receipt_data["stored_filename"]
        )

        old_receipt.file_path = (
            receipt_data["file_path"]
        )

        old_receipt.mime_type = (
            receipt_data["mime_type"]
        )

        old_receipt.file_size = (
            receipt_data["file_size"]
        )

        old_receipt.uploaded_by = (
            current_user.id
        )

    else:

        receipt = Receipt(
            transaction_id=transaction.id,
            original_filename=(
                receipt_data["original_filename"]
            ),
            stored_filename=(
                receipt_data["stored_filename"]
            ),
            file_path=(
                receipt_data["file_path"]
            ),
            mime_type=(
                receipt_data["mime_type"]
            ),
            file_size=(
                receipt_data["file_size"]
            ),
            uploaded_by=current_user.id
        )

        db.session.add(receipt)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        try:
            if os.path.exists(
                receipt_data["file_path"]
            ):
                os.remove(
                    receipt_data["file_path"]
                )
        except OSError:
            pass

        flash(
            "Receipt could not be saved.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    if old_receipt:
        flash(
            "Receipt replaced successfully.",
            "success"
        )
    else:
        flash(
            "Receipt uploaded successfully.",
            "success"
        )

    return redirect(
        url_for(
            "transactions.detail",
            transaction_id=transaction.id
        )
    )


@transactions.route(
    "/<int:transaction_id>/receipt/view"
)
@login_required
def view_receipt(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    receipt = transaction.receipt

    if not receipt:
        flash(
            "No receipt is attached to this transaction.",
            "warning"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    if not receipt.file_path:
        flash(
            "Receipt file path is missing.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    if not os.path.exists(receipt.file_path):
        flash(
            "Receipt file could not be found on the server.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    return send_file(
        receipt.file_path,
        mimetype=receipt.mime_type,
        as_attachment=False,
        download_name=receipt.original_filename
    )


@transactions.route(
    "/<int:transaction_id>/receipt/delete",
    methods=["POST"]
)
@login_required
def delete_receipt(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    receipt = transaction.receipt

    if not receipt:
        flash(
            "No receipt is attached to this transaction.",
            "warning"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    delete_receipt_file(receipt)

    try:
        db.session.delete(receipt)
        db.session.commit()

    except Exception:
        db.session.rollback()

        flash(
            "Receipt could not be deleted.",
            "danger"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    flash(
        "Receipt removed successfully.",
        "success"
    )

    return redirect(
        url_for(
            "transactions.detail",
            transaction_id=transaction.id
        )
    )


@transactions.route(
    "/<int:transaction_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    accounts = get_active_accounts()

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        ).strip().lower()

        amount_input = request.form.get(
            "amount",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        transaction_date_input = request.form.get(
            "transaction_date",
            ""
        ).strip()

        account_id_input = request.form.get(
            "account_id",
            ""
        ).strip()

        if transaction_type not in {"income", "expense"}:
            flash(
                "Please select a valid transaction type.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if not amount_input:
            flash(
                "Transaction amount is required.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        try:
            new_amount = Decimal(
                amount_input
            )
        except (InvalidOperation, ValueError):
            flash(
                "Amount must be a valid number.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if new_amount <= Decimal("0"):
            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if not description:
            flash(
                "Description is required.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if not category:
            flash(
                "Category is required.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if not transaction_date_input:
            flash(
                "Transaction date is required.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        try:
            new_date = date.fromisoformat(
                transaction_date_input
            )
        except ValueError:
            flash(
                "Invalid transaction date.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if not account_id_input:
            flash(
                "Please select a financial account.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        try:
            new_account_id = int(
                account_id_input
            )
        except (TypeError, ValueError):
            flash(
                "Invalid financial account.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        new_account = db.session.get(
            Account,
            new_account_id
        )

        if not new_account:
            flash(
                "Selected financial account was not found.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        if new_account.status != "active":
            flash(
                "Selected financial account is not active.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        old_account = None

        if transaction.account_id:
            old_account = db.session.get(
                Account,
                transaction.account_id
            )

        if not old_account:
            flash(
                "This transaction has no financial account assigned.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        old_balance = Decimal(
            str(old_account.current_balance or 0)
        )

        old_amount = Decimal(
            str(transaction.amount)
        )

        if transaction.transaction_type == "income":
            old_account.current_balance = (
                old_balance - old_amount
            )
        else:
            old_account.current_balance = (
                old_balance + old_amount
            )

        if new_account.id == old_account.id:
            new_account_balance = Decimal(
                str(old_account.current_balance or 0)
            )
        else:
            new_account_balance = Decimal(
                str(new_account.current_balance or 0)
            )

        if transaction_type == "expense":

            if new_amount > new_account_balance:
                db.session.rollback()

                flash(
                    "Insufficient balance for this expense.",
                    "danger"
                )

                return render_template(
                    "transactions/edit.html",
                    transaction=transaction,
                    accounts=accounts
                )

        if transaction_type == "income":
            new_account.current_balance = (
                new_account_balance + new_amount
            )
        else:
            new_account.current_balance = (
                new_account_balance - new_amount
            )

        transaction.transaction_type = (
            transaction_type
        )

        transaction.amount = new_amount

        transaction.description = (
            description
        )

        transaction.category = category

        transaction.transaction_date = (
            new_date
        )

        transaction.account_id = (
            new_account.id
        )

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            flash(
                "Transaction could not be updated.",
                "danger"
            )

            return render_template(
                "transactions/edit.html",
                transaction=transaction,
                accounts=accounts
            )

        flash(
            "Transaction updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "transactions.detail",
                transaction_id=transaction.id
            )
        )

    return render_template(
        "transactions/edit.html",
        transaction=transaction,
        accounts=accounts
    )


@transactions.route(
    "/<int:transaction_id>/delete",
    methods=["POST"]
)
@login_required
def delete(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:
        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    account = None

    if transaction.account_id:
        account = db.session.get(
            Account,
            transaction.account_id
        )

    if not account:
        flash(
            "This transaction has no financial account assigned.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    current_balance = Decimal(
        str(account.current_balance or 0)
    )

    transaction_amount = Decimal(
        str(transaction.amount)
    )

    if transaction.transaction_type == "income":
        account.current_balance = (
            current_balance - transaction_amount
        )
    else:
        account.current_balance = (
            current_balance + transaction_amount
        )

    receipt = transaction.receipt

    if receipt:
        delete_receipt_file(receipt)

    try:
        db.session.delete(transaction)
        db.session.commit()

    except Exception:
        db.session.rollback()

        flash(
            "Transaction could not be deleted.",
            "danger"
        )

        return redirect(
            url_for("transactions.index")
        )

    flash(
        "Transaction deleted successfully.",
        "success"
    )

    return redirect(
        url_for("transactions.index")
    )