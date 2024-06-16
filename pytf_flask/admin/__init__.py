from functools import wraps
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


admin = Blueprint('main', __name__, template_folder="templates")


@admin.before_request
def before_request():
    if request.endpoint in ('main.login', 'main.auth', 'main.logout'):
        current_app.logger.debug("Not checking for user")
        return
    current_app.logger.debug("Checking user here")
    if session.get('user') is None:
        current_app.logger.debug("No user")
        session.clear()
        return render_template('admin/login.html')


def needs_admin_community(f):
    """
    This is a decorator that confirms that session['admin_community_id'] and
    session['admin_community_name'] are in the session.

    If these are not there, then redirect to /admin/home
    :param f: The decorated function
    :return: The wrapped function
    """

    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get('admin_community_id') and session.get('admin_community_name'):
            return f(*args, **kwargs)

        return redirect(url_for('admin.communities'))

    return wrapped


from . import admin_views, download, auth
