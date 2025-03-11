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

# List of broader keywords (e.g., from your screenshot)
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
    "mental health in seniors","elderly",
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

            # Fetch video statistics
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            # Prepare dicts keyed by ID for safe lookups
            video_stats_dict = {item["id"]: item["statistics"] for item in stats_data["items"]}
            channel_stats_dict = {item["id"]: item["statistics"] for item in channel_data["items"]}

            # Collect results
            for video in videos:
                video_id = video["id"].get("videoId")
                channel_id = video["snippet"].get("channelId")

                if not video_id or not channel_id:
                    continue

                vid_stats = video_stats_dict.get(video_id, {})
                chan_stats = channel_stats_dict.get(channel_id, {})

                # Extract relevant data
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                views = int(vid_stats.get("viewCount", 0))
                subs = int(chan_stats.get("subscriberCount", 0))

                # Calculate a simple "virality factor"
                # Example: if views are >= 10 * subscribers => "viral"
                # Or store the ratio as virality_factor = views / subs (if subs > 0)
                virality_factor = 0
                if subs > 0:
                    virality_factor = views / subs

                # You can decide whether to filter only "viral" or display everything
                # For example, filter channels with fewer than 2000 subscribers
                # AND show if the virality_factor >= 10
                if subs < 2000 and virality_factor >= 10:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "ViralityFactor": round(virality_factor, 2)
                    })

        # Display results
        if all_results:
            # Sort descending by virality factor or views if desired
            all_results.sort(key=lambda x: x["ViralityFactor"], reverse=True)

            st.success(f"Found {len(all_results)} 'viral' results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Virality Factor (Views/Subs):** {result['ViralityFactor']}"
                )
                st.write("---")
        else:
            st.warning("No 'viral' results found with the current filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
