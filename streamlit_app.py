import streamlit as st
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# 🔐 Your YouTube API key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# ✅ Match brand to channel title (basic)
def is_official_channel(channel_title, brand):
    brand = re.sub(r'\W+', '', brand.lower())
    channel_title = re.sub(r'\W+', '', channel_title.lower())
    return (
        brand in channel_title or
        channel_title.startswith(brand) or
        any(kw in channel_title for kw in ['official', 'anker', 'eufy', 'belkin', 'soundcore'])
    )

# 🔎 Simplify long product names
def simplify_name(name):
    return re.sub(r'[^a-zA-Z0-9 ]', '', name)

# 🔍 Try YouTube API
def search_youtube_api(product_name, brand):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": product_name,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": 5
    }

    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return None  # will fallback

    data = response.json()
    for item in data.get("items", []):
        channel_title = item["snippet"]["channelTitle"]
        if is_official_channel(channel_title, brand):
            return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    return None

# 🔄 Fallback: Google Search scraping
def fallback_google_search(product_name, brand):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    query = f"site:youtube.com {product_name} {brand}"
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            if 'youtube.com/watch?v=' in href:
                # Clean & return the first valid link
                match = re.search(r"\/url\?q=(https:\/\/www\.youtube\.com\/watch\?v=[^&]+)", href)
                if match:
                    return match.group(1)
    except Exception as e:
        return None

    return None

# 🎯 Extract YouTube video ID
def extract_video_id(link):
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1]
    return "N/A"

# 🎥 Main video search wrapper
def get_video_link(product_name, brand):
    try:
        yt_link = search_youtube_api(product_name, brand)
        if yt_link:
            return yt_link
        # fallback if no result
        return fallback_google_search(product_name, brand) or "N/A"
    except Exception:
        return "N/A"

# 📊 Streamlit UI
st.set_page_config(page_title="Promo Video Finder", layout="wide")
st.title("📺 YouTube Promo Video Finder with Google Fallback")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Your Excel must have 'Product Name' and 'Brand' columns.")
        else:
            with st.spinner("🔍 Searching YouTube and Google..."):
                df['Official YouTube Link'] = df.apply(
                    lambda row: get_video_link(row['Product Name'], row['Brand']), axis=1
                )
                df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Done!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "youtube_links_with_ids.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
