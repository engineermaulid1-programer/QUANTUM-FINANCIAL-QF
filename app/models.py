from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


db = SQLAlchemy()


# ==========================================================
# USER
# ==========================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        default="staff"
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


# ==========================================================
# ACCOUNT
# ==========================================================

class Account(db.Model):

    __tablename__ = "accounts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    account_type = db.Column(
        db.String(50),
        nullable=False
    )

    account_number = db.Column(
        db.String(100),
        unique=True,
        nullable=True,
        index=True
    )

    opening_balance = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=0
    )

    current_balance = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=0
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="account",
        lazy=True
    )


# ==========================================================
# TRANSACTION
# ==========================================================

class Transaction(db.Model):

    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_type = db.Column(
        db.String(20),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    transaction_date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="completed"
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.id"),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    account = db.relationship(
        "Account",
        back_populates="transactions"
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    receipt = db.relationship(
        "Receipt",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan"
    )


# ==========================================================
# RECEIPT
# ==========================================================

class Receipt(db.Model):

    __tablename__ = "receipts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    file_size = db.Column(
        db.Integer,
        nullable=True
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    transaction = db.relationship(
        "Transaction",
        back_populates="receipt"
    )

    uploader = db.relationship(
        "User",
        foreign_keys=[uploaded_by]
    )
