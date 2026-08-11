from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*allowed_roles):

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            if not current_user.is_authenticated:
                return current_user.login_view

            if current_user.role not in allowed_roles:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator