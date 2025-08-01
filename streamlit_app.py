import streamlit as st
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# 🔐 Your YouTube API key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# ✅ Loose channel match
def is_official_channel(channel_title, brand):
    brand = re.sub(r'\W+', '', brand.lower())
    channel_title = re.sub(r'\W+', '', channel_title.lower())
    return (
        brand in channel_title or
        channel_title.startswith(brand) or
        any(kw in channel_title for kw in ['official', 'anker', 'eufy', 'belkin', 'soundcore'])
    )

# 🔍 YouTube API search
def search_youtube_api(product_name, brand):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": product_name,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": 5
    }

    try:
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            return None

        data = response.json()
        for item in data.get("items", []):
            channel_title = item["snippet"]["channelTitle"]
            if is_official_channel(channel_title, brand):
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    except:
        pass

    return None

# 🟡 Bing fallback
def fallback_bing_search(product_name, brand):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = f"site:youtube.com {product_name} {brand}"
    search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"

    try:
        time.sleep(1.5)
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            if 'youtube.com/watch?v=' in href:
                return href
    except Exception:
        return None

    return None

# 🎯 Extract YouTube video ID
def extract_video_id(link):
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return "N/A"

# 🔁 Master function
def get_video_link(product_name, brand):
    try:
        yt_link = search_youtube_api(product_name, brand)
        if yt_link:
            return yt_link
        return fallback_bing_search(product_name, brand) or "N/A"
    except:
        return "N/A"

# 🖼️ Streamlit UI
st.set_page_config(page_title="YouTube Promo Finder", layout="wide")
st.title("📺 Official YouTube Promo Video Finder (With Bing Fallback)")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Your Excel must have 'Product Name' and 'Brand' columns.")
        else:
            with st.spinner("🔎 Searching YouTube and Bing..."):
                df['Official YouTube Link'] = df.apply(
                    lambda row: get_video_link(row['Product Name'], row['Brand']), axis=1
                )
                df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Search complete!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "youtube_links_with_ids.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
