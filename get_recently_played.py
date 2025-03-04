import os
from datetime import datetime
import requests
import asyncpg
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

async def get_access_token():
    try:
        conn = await asyncpg.connect(database=DB_NAME,
                                     user=DB_USER,
                                     password=DB_PASSWORD,
                                     host=DB_HOST,
                                     port=5432)

        token_record = await conn.fetchrow("SELECT access_token, refresh_token FROM tokens;")
        await conn.close()

        if not token_record:
            return None

        access_token = token_record["access_token"]
        refresh_token = token_record["refresh_token"]

        # Check if the token is still valid
        headers = {"Authorization": f"Bearer {access_token}"}
        test_response = requests.get("https://api.spotify.com/v1/me", headers=headers)

        if test_response.status_code == 401:  # Token expired
            access_token = await refresh_access_token(refresh_token)

        return access_token

    except Exception as e:
        print(f"Database error: {e}")
        return None


async def refresh_access_token(refresh_token):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(url, data=data)

    if response.status_code != 200:
        return None

    new_token_data = response.json()
    new_access_token = new_token_data.get("access_token")

    if not new_access_token:
        print("Failed to refresh access token.")
        return None

    # Store the new access token in the database
    try:
        conn = await asyncpg.connect(database=DB_NAME,
                                     user=DB_USER,
                                     password=DB_PASSWORD,
                                     host=DB_HOST,
                                     port=5432)
        await conn.execute("""
            UPDATE tokens SET access_token = $1 WHERE refresh_token = $2;
        """, new_access_token, refresh_token)
        await conn.close()

        print("Access token successfully refreshed and stored.")
        return new_access_token

    except Exception as e:
        print(f"Database error while updating token: {e}")
        return None


async def store_recently_played_tracks(track_id, timestamp):
    try:
        # Convert string timestamp to datetime
        played_at = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

        conn = await asyncpg.connect(database=DB_NAME,
                                     user=DB_USER,
                                     password=DB_PASSWORD,
                                     host=DB_HOST,
                                     port=5432)
        await conn.execute("""
            INSERT INTO public.tracks_history (track_id, played_at)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
        """, track_id, played_at)

        await conn.close()
        print(f"Stored: {track_id} at {played_at}")

    except Exception as e:
        print(f"Database error: {e}")


async def get_recently_played():
    token = await get_access_token()

    if not token:
        print("No access token available")
        return None

    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Spotify API request failed")
        return None

    data = response.json()
    return [
        {"track_id": item["track"]["id"], "played_at": item["played_at"]}
        for item in data.get("items", [])
    ]


async def main():
    tracks = await get_recently_played()

    if not tracks:
        print("No recently played tracks found.")
        return

    # Store tracks
    await asyncio.gather(*(store_recently_played_tracks(track["track_id"], track["played_at"]) for track in tracks))

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
