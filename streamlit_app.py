import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup

st.title("Jumia SKU → Product Link Finder")

sku = st.text_input("Enter Jumia SKU (e.g., AI234HA0D11QVNAFAMZ):")

if st.button("Get Product Link"):
    if sku.strip():
        try:
            # Create scraper
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            
            # Search URL
            search_url = f"https://www.jumia.co.ke/catalog/?q={sku}"
            st.write(f"Searching: {search_url}")

            # Get page
            res = scraper.get(search_url)
            if res.status_code != 200:
                st.error(f"Failed to fetch page. Status code: {res.status_code}")
            else:
                soup = BeautifulSoup(res.text, "html.parser")
                product_tag = soup.select_one("a.core")  # Jumia's product card link selector

                if product_tag and "href" in product_tag.attrs:
                    product_url = "https://www.jumia.co.ke" + product_tag["href"]
                    st.success("Product Link Found!")
                    st.markdown(f"[{product_url}]({product_url})")
                else:
                    st.error("No product found for this SKU.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a SKU.")
