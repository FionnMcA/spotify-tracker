import os
import base64
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, jsonify

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
app = Flask(__name__)

scope = 'user-read-private user-read-email user-read-recently-played'
redirect_uri = 'http://127.0.0.1:5000/callback'
@app.route('/')
def index():
    return redirect(f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={redirect_uri}")

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

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token
        })



if __name__ == '__main__':
    app.run(debug=True)
