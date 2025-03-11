import streamlit as st
import requests
from datetime import datetime, timedelta
import re

# YouTube API Key
API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Utility function to parse ISO 8601 video duration
# e.g. "PT1H2M30S", "PT15M", "PT30S", etc.
def parse_duration(duration_str):
    """
    Parses an ISO 8601 duration string (e.g. 'PT1H2M30S')
    and returns the total duration in seconds.
    """
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    if not match:
        return 0  # If for some reason it doesn't match, default to 0

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

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
    "mental health in seniors",
    "elderly",
    "senior",
    "relationships",
    "motivation",
    "inspiration",
    "psychology",
    "retirement",
    "life lessons",
    "self improvement",
    "life advice",
    "golden years",
    "aging gracefully",
    "healthy aging",
    "senior lifestyle",
    "self-care for seniors",
    "senior wisdom",
    "aging advice",
    "senior health",
    "independent living",
    "wisdom advice",
    "advice for the elder",
    "life after 60",
    "senior wellness",
    "retirement lifestyle",
    "senior living tips",
    "active seniors",
    "Senior Living",
    "healthy aging",
    "Senior Health Tips"
]

if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Iterate over the list of keywords
        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            # Define search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            # Check if "items" key exists
            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [
                video["id"]["videoId"]
                for video in videos
                if "id" in video and "videoId" in video["id"]
            ]
            channel_ids = [
                video["snippet"]["channelId"]
                for video in videos
                if "snippet" in video and "channelId" in video["snippet"]
            ]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics AND content details (for duration)
            stats_params = {
                "part": "statistics,contentDetails",  # Include contentDetails
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics/content details for keyword: {keyword}")
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
            video_stats_dict = {item["id"]: item for item in stats_data["items"]}
            channel_stats_dict = {item["id"]: item["statistics"] for item in channel_data["items"]}

            # Collect results
            for video in videos:
                video_id = video["id"].get("videoId")
                channel_id = video["snippet"].get("channelId")

                if not video_id or not channel_id:
                    continue

                # Grab the entire video info (stats + contentDetails)
                vid_info = video_stats_dict.get(video_id, {})
                vid_stats = vid_info.get("statistics", {})
                content_details = vid_info.get("contentDetails", {})

                # Parse duration
                duration_str = content_details.get("duration", "PT0S")
                video_length_seconds = parse_duration(duration_str)

                # Skip if video is under 10 minutes (600 seconds)
                if video_length_seconds < 600:
                    continue

                # Channel stats
                chan_stats = channel_stats_dict.get(channel_id, {})

                # Extract relevant data
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                views = int(vid_stats.get("viewCount", 0))
                subs = int(chan_stats.get("subscriberCount", 0))

                # Calculate a simple "virality factor"
                virality_factor = 0
                if subs > 0:
                    virality_factor = views / subs

                # Filter for channels under 2k subs & virality >= 10
                if subs < 2000 and virality_factor >= 10:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "ViralityFactor": round(virality_factor, 2),
                        "DurationSec": video_length_seconds
                    })

        # Display results
        if all_results:
            # Sort descending by virality factor
            all_results.sort(key=lambda x: x["ViralityFactor"], reverse=True)

            st.success(f"Found {len(all_results)} 'viral' results (>=10 min) across all keywords!")
            for result in all_results:
                duration_in_minutes = round(result["DurationSec"] / 60, 1)
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Virality Factor (Views/Subs):** {result['ViralityFactor']}  \n"
                    f"**Video Length:** {duration_in_minutes} minutes"
                )
                st.write("---")
        else:
            st.warning("No 'viral' results found (>=10 min) with the current filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
