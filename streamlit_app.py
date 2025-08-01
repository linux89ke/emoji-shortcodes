import streamlit as st
import pandas as pd
import requests
import re

# 🔐 Your YouTube API key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# ✅ Normalize and loosely match brand to channel title
def is_official_channel(channel_title, brand):
    brand = re.sub(r'\W+', '', brand.lower())
    channel_title = re.sub(r'\W+', '', channel_title.lower())
    return brand in channel_title or channel_title.startswith(brand) or brand.startswith(channel_title)

# 🔍 Search for promo video on YouTube
def get_official_video_link(product_name, brand):
    if pd.isna(product_name) or pd.isna(brand):
        return "N/A"

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
            return "N/A"

        data = response.json()
        for item in data.get("items", []):
            channel_title = item["snippet"]["channelTitle"]
            if is_official_channel(channel_title, brand):
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    except Exception as e:
        return f"Error: {str(e)}"

    return "N/A"

# 🎯 Extract just the video ID
def extract_video_id(link):
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1]
    return "N/A"

# 🖼️ Streamlit App UI
st.set_page_config(page_title="YouTube Promo Finder", layout="wide")
st.title("📺 Official YouTube Promo Video Finder")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Your Excel must have 'Product Name' and 'Brand' columns.")
        else:
            with st.spinner("🔎 Searching YouTube for official videos..."):
                df['Official YouTube Link'] = df.apply(
                    lambda row: get_official_video_link(row['Product Name'], row['Brand']), axis=1
                )
                df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Search complete!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "youtube_links_with_ids.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
