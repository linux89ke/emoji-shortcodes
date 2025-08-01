import streamlit as st
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# --- 1. Helper Functions ---

def clean_product_name(product_name):
    """Simplifies product name for better search results."""
    product_name = re.sub(r' \(.+\)', '', product_name)
    noise_words = [
        'black', 'white', 'blue', 'green', 'gray', 'grey', 'gold', 'silver',
        'portable', 'bluetooth speaker', 'power bank', 'earbuds', 'headphones',
        'true wireless', 'usb-c hub', r'\b\d{1,2}W\b', r'\b\d{1,5}mAh\b', r'\b\d-in-\d\b'
    ]
    for noise in noise_words:
        product_name = re.sub(r'\b' + noise + r'\b', '', product_name, flags=re.IGNORECASE)
    return ' '.join(product_name.split())

def is_official_channel_name(channel_name, brand):
    brand_norm = re.sub(r'\W+', '', brand.lower())
    channel_norm = re.sub(r'\W+', '', channel_name.lower())
    return (
        brand_norm in channel_norm or
        channel_norm.startswith(brand_norm) or
        any(f"{brand_norm}{suffix}" in channel_norm for suffix in ['official', 'global', 'us'])
    )

def extract_video_id(link):
    """Extracts video ID from a YouTube URL."""
    if isinstance(link, str) and "watch?v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return "N/A"

def scrape_bing_or_google(query):
    """Scrapes Bing or Google for YouTube links."""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    try:
        time.sleep(1)
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        video_links = []
        for link in links:
            href = link['href']
            match = re.search(r"(https:\/\/www\.youtube\.com\/watch\?v=[\w\-]+)", href)
            if match:
                video_links.append(match.group(1))
        return list(set(video_links))  # Unique
    except Exception:
        return []

def find_video_without_api(product_name, brand):
    """Finds the most likely official YouTube promo video using scraping only."""
    cleaned = clean_product_name(product_name)
    queries = [
        f'site:youtube.com "{brand} {cleaned}" official',
        f'site:youtube.com "{brand} {product_name}" launch trailer',
        f'site:youtube.com "{brand} {cleaned}" promo',
        f'site:youtube.com "{brand} {cleaned}"'
    ]

    for q in queries:
        results = scrape_bing_or_google(q)
        if results:
            return results[0]  # Return first found video
    return "N/A"

# --- 2. Streamlit UI ---

st.set_page_config(page_title="YouTube Promo Finder (No API)", layout="wide")
st.title("🔍 Official YouTube Promo Finder (API-Free)")
st.info("Uses Google/Bing scraping to find official YouTube promo videos based on product and brand.")

uploaded_file = st.file_uploader("📤 Upload Excel (.xlsx) with 'Product Name' and 'Brand' columns", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if 'Product Name' not in df.columns or 'Brand' not in df.columns:
            st.error("❌ Your Excel must have 'Product Name' and 'Brand' columns.")
        else:
            progress = st.progress(0)
            total = len(df)
            video_links = []

            for idx, row in df.iterrows():
                link = find_video_without_api(row['Product Name'], row['Brand'])
                video_links.append(link)
                progress.progress((idx + 1) / total)

            df['Official YouTube Link'] = video_links
            df['YouTube Video ID'] = df['Official YouTube Link'].apply(extract_video_id)

            st.success("✅ Done! Found YouTube links using Bing/Google.")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV with YouTube Links", csv, "youtube_links_no_api.csv", "text/csv")
    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
