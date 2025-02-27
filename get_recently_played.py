import requests


def get_recently_played():
    url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = {
        "Authorization": "Bearer <ACCESS_TOKEN>",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        tracks = [
            {"track_uri": item["track"]["uri"], "played_at": item["played_at"]}
            for item in data.get("items", [])
        ]
        return tracks
    else:
        return None

data = get_recently_played()
if data:
    print(data)