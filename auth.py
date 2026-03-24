# auth.py

import os
from functools import wraps
from flask import session, redirect, request
import requests

# 容器內部通訊用（Flask → Keycloak）
KEYCLOAK_INTERNAL_URL = os.environ.get('KEYCLOAK_URL', 'http://keycloak:8080')

# 瀏覽器跳轉用（必須是 localhost）
KEYCLOAK_PUBLIC_URL = os.environ.get('KEYCLOAK_PUBLIC_URL', 'http://localhost:8080')

REALM = os.environ.get('KEYCLOAK_REALM', 'argus-realm')
CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'argus-client')
CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET')

# 內部用（token 交換）
TOKEN_URL    = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/userinfo"

# 外部用（瀏覽器跳轉）
AUTH_URL     = f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}/protocol/openid-connect/auth"
LOGOUT_URL   = f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}/protocol/openid-connect/logout"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def login():
    return redirect(
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost:5000/callback"
        f"&scope=openid profile email"
    )

def callback():
    code = request.args.get('code')
    resp = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': 'http://localhost:5000/callback'
    })
    tokens = resp.json()
    session['access_token'] = tokens['access_token']
    return redirect('/')

def logout():
    session.clear()
    return redirect(LOGOUT_URL + "?redirect_uri=http://localhost:5000")