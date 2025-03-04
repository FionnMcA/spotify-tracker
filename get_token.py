import os
import base64
from flask import Flask, redirect, request, jsonify
import asyncpg
import asyncio
import requests
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
app = Flask(__name__)

scope = 'user-read-private user-read-email user-read-recently-played'
redirect_uri = 'http://127.0.0.1:5000/callback'

# Store tokens in db
async def store_data(access_token, refresh_token):
    try:
        conn = await asyncpg.connect(database=DB_NAME,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                host=DB_HOST,
                                port=5432)

        await conn.execute("""
            INSERT INTO tokens (access_token, refresh_token)
            VALUES ($1, $2)
        """, access_token, refresh_token)

        await conn.close()
        print("Tokens stored")


    except Exception as e:
        print(e)

# Redirect to spotify Auth page
@app.route('/')
def index():
    return redirect(f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={redirect_uri}")

# From spotify auth, redirect to call back with the code in the url
# Then take the code and exchange it for an access and refresh token
# The store the access and refresh token in my database
@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    token_url = f'https://accounts.spotify.com/api/token'
    payload = {
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=payload, headers=headers)
    token_info = response.json()

    if response.status_code == 200:
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')

        print(f"Access Token: {access_token}", flush=True)
        print(f"Refresh Token: {refresh_token}", flush=True)

        asyncio.run(store_data(access_token, refresh_token))

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token
        })

if __name__ == '__main__':
    app.run(debug=True)
