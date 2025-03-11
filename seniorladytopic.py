import requests

API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
params = {
    "part": "snippet",
    "q": "test",      # a very generic keyword
    "type": "video",
    "maxResults": 5,
    "key": API_KEY
}
resp = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
data = resp.json()
print(data)
