import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup

# Function to get Jumia product link from SKU
def jumia_link_from_sku(sku):
    url = f"https://www.jumia.co.ke/catalog/?q={sku}"
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    })
    r = scraper.get(url)

    if r.status_code != 200:
        return None, f"Error: Received status code {r.status_code}"

    soup = BeautifulSoup(r.text, "html.parser")
    product = soup.select_one("a.core")
    
    if product and product.get("href"):
        link = "https://www.jumia.co.ke" + product["href"]
        return link, None
    return None, "No product found for this SKU."

# Streamlit UI
st.title("🔍 Jumia SKU to Product Link Finder")
st.write("Paste a Jumia SKU below to get the product link.")

sku_input = st.text_input("Enter SKU (e.g., AI234HA0D11QVNAFAMZ):")

if st.button("Search"):
    if sku_input.strip():
        link, error = jumia_link_from_sku(sku_input.strip())
        if link:
            st.success("Product Found!")
            st.markdown(f"[Click here to view product]({link})")
        else:
            st.error(error)
    else:
        st.warning("Please enter a SKU.")
