import streamlit as st
import pandas as pd
import requests

# ✅ Your YouTube API Key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# 🔍 Check if channel title looks official (brand included, stripped spacing/caps)
def is_official_channel(channel_title, brand):
    brand = brand.lower().replace(" ", "")
    channel_title = channel_title.lower().replace(" ", "")
    return brand in channel_title

# 📺 Get official YouTube video link
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
                video_id = item["id"]["videoId"]
                return f"https://www.youtube.com/watch?v={video_id}"
    except:
        return "N/A"

    return "N/A"

# 🔎 Extract YouTube video ID
def extract_video_id(link):
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1]
    return "N/A"

# 🖼️ Streamlit UI
st.set_page_config(page_title="YouTube Promo Finder", layout="wide")
st.title("📺 Official YouTube Promo Video Finder (Any Brand)")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand'", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Validate expected columns
        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Excel must contain 'Product Name' and 'Brand' columns.")
        else:
            with st.spinner("🔎 Searching YouTube..."):
                df['Official YouTube Link'] = df.apply(
                    lambda row: get_official_video_link(row['Product Name'], row['Brand']), axis=1
                )
                df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Done!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "youtube_links_with_ids.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
