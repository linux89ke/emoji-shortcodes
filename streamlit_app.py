import streamlit as st
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# --- Configuration ---
YOUTUBE_API_KEY = "AIzaSyCRcdZRjuSs7eQXXYHVJ1aMbzrJHxtjOvY"

# --- 1. Helper Functions for Cleaning and Scoring ---

def clean_product_name(product_name):
    product_name = re.sub(r' \(.+\)', '', product_name)
    common_noise = [
        'black', 'white', 'blue', 'green', 'gray', 'grey', 'gold', 'silver',
        'portable', 'bluetooth speaker', 'power bank', 'earbuds', 'headphones',
        'true wireless', 'usb-c hub', r'\b\d{1,2}W\b', r'\b\d{1,5}mAh\b', r'\b\d-in-\d\b'
    ]
    for noise in common_noise:
        product_name = re.sub(r'\b' + noise + r'\b', '', product_name, flags=re.IGNORECASE)
    return ' '.join(product_name.split())

def score_video(video_title, channel_title, brand):
    score = 0
    title = video_title.lower()
    channel = channel_title.lower()
    brand_lower = brand.lower()

    if any(kw in title for kw in ['official', 'introducing', 'launch', 'hands-on', 'trailer', 'ad']):
        score += 20
    if any(kw in title for kw in ['review', 'unboxing', 'vs', 'test', 'how to', 'support', 'guide']):
        score -= 15
    if channel == brand_lower or channel == f"{brand_lower} official":
        score += 10
    if brand_lower in title:
        score += 5

    return score

# --- 2. Core Search and Verification Logic ---

def is_official_channel(channel_title, brand):
    brand_norm = re.sub(r'\W+', '', brand.lower())
    channel_norm = re.sub(r'\W+', '', channel_title.lower())
    return (
        brand_norm in channel_norm or
        channel_norm.startswith(brand_norm) or
        any(f"{brand_norm}{suffix}" in channel_norm for suffix in ['official', 'global', 'us'])
    )

def search_youtube_api(query, max_results=5):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        st.warning(f"API request failed: {e}")
        return []

def get_video_details_by_id(video_id):
    details_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }
    try:
        response = requests.get(details_url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        if items:
            return items[0]['snippet']
    except requests.exceptions.RequestException as e:
        st.warning(f"API request for video details failed: {e}")
    return None

def fallback_bing_search(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    video_ids = []
    try:
        time.sleep(1)
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', href)
            if match:
                video_ids.append(match.group(1))
        return list(set(video_ids))
    except Exception:
        return []

# --- 3. Master Orchestrator Function ---

def find_official_video(product_name, brand):
    cleaned_name = clean_product_name(product_name)
    search_queries = [
        f'"{brand} {cleaned_name}" official launch',
        f'"{brand} {cleaned_name}" official trailer',
        f'"{brand} {product_name}"',
        f'"{brand} {cleaned_name}"',
    ]

    best_video = None
    highest_score = -99

    for query in search_queries:
        results = search_youtube_api(query)
        for item in results:
            snippet = item['snippet']
            channel_title = snippet['channelTitle']
            if is_official_channel(channel_title, brand):
                video_title = snippet['title']
                current_score = score_video(video_title, channel_title, brand)
                if current_score > highest_score:
                    highest_score = current_score
                    best_video = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        if best_video and highest_score > 10:
            return best_video

    bing_query = f'site:youtube.com "{brand} {cleaned_name}"'
    video_ids = fallback_bing_search(bing_query)
    for video_id in video_ids[:3]:
        details = get_video_details_by_id(video_id)
        if details and is_official_channel(details['channelTitle'], brand):
            return f"https://www.youtube.com/watch?v={video_id}"

    return best_video or "N/A"

# --- 4. Utility and Streamlit UI ---

def extract_video_id(link):
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return "N/A"

st.set_page_config(page_title="YouTube Promo Finder", layout="wide")
st.title("📺 Official YouTube Promo Video Finder")
st.info("This version uses YouTube API + Bing fallback with smart scoring for best accuracy.")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Your Excel must have 'Product Name' and 'Brand' columns.")
        else:
            progress_bar = st.progress(0)
            total_rows = len(df)
            results = []

            for index, row in df.iterrows():
                link = find_official_video(row['Product Name'], row['Brand'])
                results.append(link)
                progress_bar.progress((index + 1) / total_rows)

            df['Official YouTube Link'] = results
            df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Search complete!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Results as CSV", csv, "youtube_links_with_ids.csv", "text/csv")
    except Exception as e:
        st.error(f"An error occurred: {e}")
