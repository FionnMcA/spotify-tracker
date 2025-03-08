import os
from dotenv import load_dotenv
import json
import asyncpg
import asyncio
from datetime import datetime

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# function to change the URI into the track id (just remove the start of the string)
def extract_track_id(track_uri):
    if track_uri.startswith("spotify:track:"):
        return track_uri.split(":")[-1]
    return None

# Load in the extended history json files and extract the uri (convert into a id) and the timestamp (converted to a datetime object)
async def extract_listening_history(filepath):
    try:
        with open(filepath, "r") as file:
            data = json.load(file)

        tracks_history = []
        for entry in data:
            if "spotify_track_uri" in entry and entry["spotify_track_uri"]:
                timestamp = entry.get("ts")
                if timestamp:
                    formatted_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                else:
                    formatted_time = None

                track_id = extract_track_id(entry["spotify_track_uri"])
                if track_id and formatted_time:
                    tracks_history.append((track_id, formatted_time))

        await store_extended_history(tracks_history)

    except Exception as e:
        print(e)

async def store_extended_history(tracks_history):

    if not tracks_history:
        print("No history")

    try:
        conn = await asyncpg.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
        )

        await conn.executemany(
            """
            INSERT INTO public.tracks_history (track_id, played_at)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
            """,
            tracks_history
        )

        await conn.close()
        print(f"Stored {len(tracks_history)} tracks.")

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    files = [
        "Streaming_History_Audio_2018-2020_0.json",
        "Streaming_History_Audio_2020-2021_1.json",
        "Streaming_History_Audio_2021-2022_2.json",
        "Streaming_History_Audio_2022-2023_5.json",
        "Streaming_History_Audio_2022_3.json",
        "Streaming_History_Audio_2022_4.json",
        "Streaming_History_Audio_2023-2024_7.json",
        "Streaming_History_Audio_2023_6.json",
        "Streaming_History_Audio_2024-2025_8.json",
        "Streaming_History_Audio_2025_9.json",
    ]
    for file in files:
        filepath = f"Spotify Extended Streaming History/{file}"
        asyncio.run(extract_listening_history(filepath))