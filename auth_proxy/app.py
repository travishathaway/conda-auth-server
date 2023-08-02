"""
OAuth2 client used for testing purposes only.

Do not use this code in production!
"""
import os
import time
import json

import redis
import requests
from flask import (
    Flask, url_for, session, redirect, Response, request, jsonify
)
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

app.config.update({
    # Add OAuth values
    'CONDA_AUTH_CLIENT_ID': os.getenv('CONDA_AUTH_CLIENT_ID'),
    'CONDA_AUTH_CLIENT_SECRET': os.getenv('CONDA_AUTH_CLIENT_SECRET'),
    'CONDA_AUTH_API_BASE_URL': os.getenv('CONDA_AUTH_API_BASE_URL'),
    'CONDA_AUTH_ACCESS_TOKEN_URL': os.getenv('CONDA_AUTH_ACCESS_TOKEN_URL'),
    'CONDA_AUTH_AUTHORIZE_URL': os.getenv('CONDA_AUTH_AUTHORIZE_URL'),
    'CONDA_AUTH_CLIENT_KWARGS': {'scope': 'conda'},

    # Flask
    'SECRET_KEY': os.getenv('SECRET_KEY'),

    # Channel Config
    'CHANNEL_URL': os.getenv('CHANNEL_URL')
})

redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0)
oauth = OAuth(app)
conda_auth = oauth.register('conda_auth', {})


@app.route('/login')
def login():
    if session.get('token'):
        return redirect('/')

    redirect_uri = url_for('authorize', _external=True)

    return conda_auth.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    resp = redirect('/login')

    return resp


@app.route('/authorize')
def authorize():
    token = conda_auth.authorize_access_token()
    redis_client.set(token["access_token"], json.dumps(token))
    # return a request showing the access token to copy and paste
    return jsonify({"access_token": token})


def _proxy(path, **kwargs):
    resp = requests.request(
        method=request.method,
        url=f'{app.config["CHANNEL_URL"]}/{path}',
        data=request.get_data(),
        params=request.args,
        allow_redirects=False
    )

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


def is_valid_token(token: str) -> bool:
    """
    Checks to see if the token exists and is not expired.
    """
    token_data = redis_client.get(token)

    if token_data is None:
        return False

    try:
        token_data = json.loads(token_data)
    except json.JSONDecodeError:
        return False

    if not token_data:
        return False

    if token_data["expires_at"] < int(time.time()):
        return False

    return True


@app.route('/channel', methods=['DELETE', 'GET', 'POST', 'PUT', 'OPTION'])
@app.route('/channel/<path:path>', methods=['DELETE', 'GET', 'POST', 'PUT', 'OPTION'])
def api(path=""):
    if not request.headers.get("Authorization"):
        return redirect('/login')

    token_parts = request.headers["Authorization"].split()

    if len(token_parts) < 2:
        return redirect('/login')

    token = token_parts[1].strip()

    if is_valid_token(token):
        return _proxy(path)

    return redirect('/login')


if __name__ == '__main__':
    app.run()
