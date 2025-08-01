import streamlit as st
import pandas as pd
import requests

# 🔐 Your YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# 🔍 Get official YouTube video link from brand channel
def get_official_video_link(product_name, brand):
    brand = brand.lower().strip()

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
            channel_title = item['snippet']['channelTitle'].lower()
            if brand in channel_title:
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    except Exception:
        return "N/A"

    return "N/A"

# 🧱 Extract video ID from YouTube link
def extract_video_id(link):
    if link.startswith("https://www.youtube.com/watch?v="):
        return link.split("v=")[-1]
    return "N/A"

# 🖼️ Streamlit UI
st.set_page_config(page_title="YouTube Promo Finder", layout="wide")
st.title("📺 Official YouTube Promo Video Finder")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Excel must contain 'Product Name' and 'Brand' columns.")
        else:
            with st.spinner("🔍 Searching YouTube..."):
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
