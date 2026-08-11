from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_migrate import Migrate

from .config import Config
from .models import db, User

login_manager = LoginManager()
migrate = Migrate()

def create_app():

    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth.routes import auth
    from .dashboard.routes import dashboard
    from .transactions.routes import transactions
    from .users.routes import users
    from .accounts.routes import accounts
    from .reports.routes import reports

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(transactions)
    app.register_blueprint(users)
    app.register_blueprint(accounts)
    app.register_blueprint(reports)

    @app.route('/')
    def home():
        return redirect(url_for('dashboard.index'))

    return app
