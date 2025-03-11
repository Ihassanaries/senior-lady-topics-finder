import streamlit as st
import requests

# YouTube API Key
API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool (Broader Search)")

# Keywords
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

def youtube_search(query):
    """
    Searches YouTube for a given query string.
    Returns the raw JSON data (items) or an empty list on failure/no results.
    """
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "relevance",   # broader, more flexible matches
        "maxResults": 50,       # max allowed is 50
        "key": API_KEY
    }
    r = requests.get(YOUTUBE_SEARCH_URL, params=params)
    data = r.json()
    return data.get("items", [])

if st.button("Fetch Data"):
    try:
        all_results = []

        for kw in keywords:
            st.write(f"### Searching for keyword: '{kw}'")
            
            # 1) Try the entire keyword as one query
            main_query_items = youtube_search(kw)

            # If no results, try each word in the keyword separately
            if not main_query_items:
                # e.g. "retirement planning" -> ["retirement", "planning"]
                sub_queries = kw.split()
                sub_query_items = []
                for word in sub_queries:
                    items = youtube_search(word)
                    sub_query_items.extend(items)
                
                # Combine results (avoid duplicates by using a dict keyed by videoId)
                combined_dict = {}
                for item in sub_query_items:
                    vid_id = item["id"].get("videoId")
                    if vid_id:
                        combined_dict[vid_id] = item
                final_items = list(combined_dict.values())
                
                if not final_items:
                    st.warning(f"No results found for '{kw}' or its sub-words.")
                    continue
                else:
                    st.write(f"No direct matches for '{kw}' — found {len(final_items)} results by splitting words.")
                    relevant_items = final_items
            else:
                st.write(f"Found {len(main_query_items)} results for '{kw}'.")
                relevant_items = main_query_items

            # Now get videoIds and channelIds from relevant items
            video_ids = [item["id"]["videoId"] for item in relevant_items if "videoId" in item["id"]]
            channel_ids = [item["snippet"]["channelId"] for item in relevant_items if "snippet" in item and "channelId" in item["snippet"]]

            # If none found, skip
            if not video_ids or not channel_ids:
                st.warning(f"Skipping '{kw}' due to missing video/channel data.")
                continue

            # 2) Fetch video statistics
            vid_params = {
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            vid_resp = requests.get(YOUTUBE_VIDEO_URL, params=vid_params).json()
            if "items" not in vid_resp or not vid_resp["items"]:
                st.warning(f"Failed to fetch video statistics for '{kw}'.")
                continue

            # 3) Fetch channel statistics
            chan_params = {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY
            }
            chan_resp = requests.get(YOUTUBE_CHANNEL_URL, params=chan_params).json()
            if "items" not in chan_resp or not chan_resp["items"]:
                st.warning(f"Failed to fetch channel statistics for '{kw}'.")
                continue

            # Create dictionaries for easy lookup
            video_stats_dict = {item["id"]: item["statistics"] for item in vid_resp["items"]}
            channel_stats_dict = {item["id"]: item["statistics"] for item in chan_resp["items"]}

            # 4) Combine & filter
            for item in relevant_items:
                vid_id = item["id"].get("videoId")
                chan_id = item["snippet"].get("channelId")
                if not vid_id or not chan_id:
                    continue

                title = item["snippet"].get("title", "N/A")
                description = item["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={vid_id}"

                vid_stats = video_stats_dict.get(vid_id, {})
                chan_stats = channel_stats_dict.get(chan_id, {})

                views = int(vid_stats.get("viewCount", 0))
                subs = int(chan_stats.get("subscriberCount", 0))

                # Filter channels with < 2000 subscribers
                if subs < 2000:
                    all_results.append({
                        "Keyword": kw,
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })

        # Display final results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for res in all_results:
                st.markdown(
                    f"**Keyword:** {res['Keyword']}  \n"
                    f"**Title:** {res['Title']}  \n"
                    f"**Description:** {res['Description']}  \n"
                    f"**URL:** [Watch Video]({res['URL']})  \n"
                    f"**Views:** {res['Views']}  \n"
                    f"**Subscribers:** {res['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 2,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
