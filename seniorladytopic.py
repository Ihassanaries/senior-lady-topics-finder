import streamlit as st
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# YouTube API constants
API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# List of keywords
keywords = [
   "retirement planning",
    "how life has changed",
    "timeless advice",
    "life advice",
    "advice from elders",
    "wisdom from experience",
    "life lessons",
    "life after 70",
    "aging gracefully",
    "cleaning tips",
    "senior living tips",
    "living alone after 70",
    "decluttering tips for seniors",
    "habits to quit after 70",
    "senior lifestyle tips",
    "healthy aging tips",
    "declutter your home",
    "wellness for seniors",
    "senior safety tips",
    "healthy lifestyle",
    "relationships in later life",
    "mental health in seniors"
]

def fetch_keyword_data(keyword, start_date, session):
    results = []
    st.write(f"Searching for keyword: {keyword}")

    # Build search parameters and get search results
    search_params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": start_date,
        "maxResults": 5,
        "key": API_KEY,
    }
    response = session.get(YOUTUBE_SEARCH_URL, params=search_params)
    response.raise_for_status()
    data = response.json()

    if not data.get("items"):
        st.warning(f"No videos found for keyword: {keyword}")
        return results

    videos = data["items"]

    # Extract video and channel IDs
    video_ids = [video["id"]["videoId"] for video in videos if video.get("id", {}).get("videoId")]
    channel_ids = [video["snippet"]["channelId"] for video in videos if video.get("snippet", {}).get("channelId")]

    if not video_ids or not channel_ids:
        st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
        return results

    # Fetch video statistics
    stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
    stats_response = session.get(YOUTUBE_VIDEO_URL, params=stats_params)
    stats_response.raise_for_status()
    stats_data = stats_response.json()
    if not stats_data.get("items"):
        st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
        return results

    # Fetch channel statistics
    channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
    channel_response = session.get(YOUTUBE_CHANNEL_URL, params=channel_params)
    channel_response.raise_for_status()
    channel_data = channel_response.json()
    if not channel_data.get("items"):
        st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
        return results

    # Create dictionaries for stats matching
    video_stats = {item["id"]: item["statistics"] for item in stats_data["items"] if "id" in item}
    channel_stats = {item["id"]: item["statistics"] for item in channel_data["items"] if "id" in item}

    # Merge data safely by matching IDs
    for video in videos:
        vid = video["id"].get("videoId")
        chan = video["snippet"].get("channelId")
        if not vid or not chan:
            continue

        stats = video_stats.get(vid, {})
        chan_stats = channel_stats.get(chan, {})

        title = video["snippet"].get("title", "N/A")
        description = video["snippet"].get("description", "")[:200]
        video_url = f"https://www.youtube.com/watch?v={vid}"
        views = int(stats.get("viewCount", 0))
        subs = int(chan_stats.get("subscriberCount", 0))

        # Use threshold of fewer than 2000 subscribers as per goal
        if subs < 2000:
            results.append({
                "Title": title,
                "Description": description,
                "URL": video_url,
                "Views": views,
                "Subscribers": subs
            })
    return results

if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []
        with requests.Session() as session:
            # Use ThreadPoolExecutor to process keywords concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_keyword = {executor.submit(fetch_keyword_data, keyword, start_date, session): keyword for keyword in keywords}
                for future in as_completed(future_to_keyword):
                    all_results.extend(future.result())

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 2,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
