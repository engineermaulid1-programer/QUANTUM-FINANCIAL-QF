import os
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-change-this-before-production"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(
            BASE_DIR,
            "instance",
            "qf.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False