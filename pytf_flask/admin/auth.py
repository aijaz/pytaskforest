import json

from flask import (
    current_app,
    redirect,
    session,
    url_for,
)

from . import admin


@admin.route('/login')
def login():
    redirect_uri = url_for('admin.auth', _external=True)
    return current_app.config['oauth'].google.authorize_redirect(redirect_uri)


@admin.route('/auth')
def auth():
    token = current_app.config['oauth'].google.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect('/admin/home')


@admin.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/admin/home')
