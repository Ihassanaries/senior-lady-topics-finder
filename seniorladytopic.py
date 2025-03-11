import streamlit as st
import requests

API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

st.title("Minimal YouTube Search Debug")

keyword = st.text_input("Enter a keyword", "retirement planning")

if st.button("Search"):
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "relevance",
        "maxResults": 5,
        "key": API_KEY
    }
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params)
    data = resp.json()

    st.write("**Search Parameters**:", params)
    st.write("**Raw Response**:", data)

    if "error" in data:
        st.error(f"API Error: {data['error']}")
    else:
        items = data.get("items", [])
        st.write(f"**Items returned**: {len(items)}")
        for i, item in enumerate(items):
            st.write(f"**Item {i}**:", item)
