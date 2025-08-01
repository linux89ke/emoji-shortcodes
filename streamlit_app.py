import streamlit as st
import pandas as pd
import requests

# ✅ Your YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# 🔍 Search YouTube for brand-official video
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
            if brand in channel_title:  # Check if brand name appears in channel
                video_id = item['id']['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"

    except Exception:
        return "N/A"

    return "N/A"

# 🖼️ Streamlit UI
st.set_page_config(page_title="Universal Brand YouTube Promo Finder", layout="wide")
st.title("📺 Find Official YouTube Promo Videos for Any Brand")

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

            st.success("✅ Done!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Results", csv, "youtube_links.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
