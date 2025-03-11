import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# List of broader keywords
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

if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            # Break keyword into individual words for partial matching
            keyword_parts = keyword.lower().split()

            # Define search parameters
            # - order='relevance' tends to yield more general matches
            search_params = {
                "part": "snippet",
                "q": keyword,  # We still pass the entire keyword to the API
                "type": "video",
                "order": "relevance",
                "publishedAfter": start_date,
                "maxResults": 10,  # Increase to 10 for slightly broader coverage
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = []
            channel_ids = []

            # Locally check if any part of the keyword is in the title or description
            filtered_videos = []
            for vid in videos:
                snippet = vid.get("snippet", {})
                title_text = snippet.get("title", "").lower()
                desc_text = snippet.get("description", "").lower()

                # If ANY word from the keyword is in title or description, keep it
                if any(part in title_text or part in desc_text for part in keyword_parts):
                    filtered_videos.append(vid)

            if not filtered_videos:
                st.warning(f"No partial matches in title/description for: {keyword}")
                continue

            # Collect IDs for stats
            video_ids = [v["id"]["videoId"] for v in filtered_videos if "videoId" in v["id"]]
            channel_ids = [v["snippet"]["channelId"] for v in filtered_videos if "channelId" in v["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics
            stats_params = {
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY
            }
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            # Prepare dicts keyed by ID for safe lookups
            video_stats_dict = {item["id"]: item["statistics"] for item in stats_data["items"]}
            channel_stats_dict = {item["id"]: item["statistics"] for item in channel_data["items"]}

            # Collect results
            for v in filtered_videos:
                video_id = v["id"].get("videoId")
                channel_id = v["snippet"].get("channelId")

                if not video_id or not channel_id:
                    continue

                title = v["snippet"].get("title", "N/A")
                description = v["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                vid_stats = video_stats_dict.get(video_id, {})
                chan_stats = channel_stats_dict.get(channel_id, {})

                views = int(vid_stats.get("viewCount", 0))
                subs = int(chan_stats.get("subscriberCount", 0))

                # Filter channels with fewer than 2,000 subs
                if subs < 2000:
                    all_results.append({
                        "Keyword": keyword,
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Keyword:** {result['Keyword']}  \n"
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
