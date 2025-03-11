import streamlit as st
import requests
from datetime import datetime, timedelta
import re
from collections import Counter
import pandas as pd
import altair as alt
from concurrent.futures import ThreadPoolExecutor, as_completed

# YouTube API Key
API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"  # Replace with your actual API key
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

def fetch_data_for_keyword(keyword, start_date):
    """
    Fetches and processes data for a single keyword.
    Returns a list of 'viral' video entries that meet the criteria:
      - Video >= 10 minutes
      - Channel subscribers < 2000
      - Views >= 5 × subscribers (virality factor >= 5)
    """
    results = []
    try:
        # 1) Search for videos
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 5,
            "key": API_KEY,
        }
        response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
        data = response.json()

        if "items" not in data or not data["items"]:
            return results  # No videos found

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
            return results

        # 2) Fetch video stats + content details (for duration)
        stats_params = {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": API_KEY
        }
        stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
        stats_data = stats_response.json()
        if "items" not in stats_data or not stats_data["items"]:
            return results

        # 3) Fetch channel stats
        channel_params = {
            "part": "statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY
        }
        channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
        channel_data = channel_response.json()
        if "items" not in channel_data or not channel_data["items"]:
            return results

        # Prepare dicts keyed by ID for safe lookups
        video_stats_dict = {item["id"]: item for item in stats_data["items"]}
        channel_stats_dict = {item["id"]: item["statistics"] for item in channel_data["items"]}

        # 4) Filter + collect results
        for video in videos:
            video_id = video["id"].get("videoId")
            channel_id = video["snippet"].get("channelId")

            if not video_id or not channel_id:
                continue

            vid_info = video_stats_dict.get(video_id, {})
            vid_stats = vid_info.get("statistics", {})
            content_details = vid_info.get("contentDetails", {})

            # Parse duration and skip videos < 10 minutes
            duration_str = content_details.get("duration", "PT0S")
            video_length_seconds = parse_duration(duration_str)
            if video_length_seconds < 600:  # 10 minutes = 600 seconds
                continue

            # Channel stats
            chan_stats = channel_stats_dict.get(channel_id, {})
            subs = int(chan_stats.get("subscriberCount", 0))

            # Basic video info
            title = video["snippet"].get("title", "N/A")
            description = video["snippet"].get("description", "")[:200]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            views = int(vid_stats.get("viewCount", 0))

            # Virality factor (5× threshold)
            virality_factor = 0
            if subs > 0:
                virality_factor = views / subs

            # If channel < 2000 subs & video is 5× more views than subs
            if subs < 2000 and virality_factor >= 5:
                results.append({
                    "Keyword": keyword,
                    "Title": title,
                    "Description": description,
                    "URL": video_url,
                    "Views": views,
                    "Subscribers": subs,
                    "ViralityFactor": round(virality_factor, 2),
                    "DurationSec": video_length_seconds
                })

    except Exception:
        # Ignore or log individual keyword errors
        pass

    return results

# ----------------------------------------------
# Streamlit UI
# ----------------------------------------------
st.title("YouTube Viral Topics Tool")

days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

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
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # --------------------------------------
        # 1) Concurrently fetch data per keyword
        # --------------------------------------
        st.write("Fetching data, please wait...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_data_for_keyword, kw, start_date): kw for kw in keywords}
            for future in as_completed(futures):
                kw_results = future.result()
                all_results.extend(kw_results)

        # --------------------------------------
        # 2) Process and display results
        # --------------------------------------
        if all_results:
            # Sort descending by ViralityFactor
            all_results.sort(key=lambda x: x["ViralityFactor"], reverse=True)

            st.success(f"Found {len(all_results)} 'viral' results (>=10 min) across all keywords!")
            for result in all_results:
                duration_in_minutes = round(result["DurationSec"] / 60, 1)
                st.markdown(
                    f"**Keyword:** {result['Keyword']}  \n"
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Virality Factor (Views/Subs):** {result['ViralityFactor']}  \n"
                    f"**Video Length:** {duration_in_minutes} minutes"
                )
                st.write("---")

            # --------------------------------------
            # 3) Additional Analysis with Pandas
            # --------------------------------------
            df = pd.DataFrame(all_results)

            # (A) Show a bar chart of average virality factor by keyword
            st.write("### Average Virality Factor by Keyword")
            group_vf = df.groupby("Keyword")["ViralityFactor"].mean().reset_index()
            group_vf.columns = ["Keyword", "AvgViralityFactor"]

            chart_vf = alt.Chart(group_vf).mark_bar().encode(
                x=alt.X("Keyword:N", sort="-y"),
                y=alt.Y("AvgViralityFactor:Q")
            ).properties(width=600)
            st.altair_chart(chart_vf, use_container_width=True)

            # (B) Simple text analysis: top words in viral video titles
            def clean_text(text):
                return re.sub(r'[^\w\s]', '', text.lower())

            all_titles = " ".join(clean_text(title) for title in df["Title"])
            words = all_titles.split()
            word_freq = Counter(words).most_common(20)

            if word_freq:
                st.write("### Top 20 Words in Viral Video Titles (≥10 min, Virality ≥5)")
                word_df = pd.DataFrame(word_freq, columns=["Word", "Frequency"])
                st.dataframe(word_df)

                # Optional bar chart for top words
                chart_words = alt.Chart(word_df).mark_bar().encode(
                    x=alt.X("Word:N", sort="-y"),
                    y="Frequency:Q"
                ).properties(width=600)
                st.altair_chart(chart_words, use_container_width=True)

        else:
            st.warning("No 'viral' results found (≥10 min) with the current filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
