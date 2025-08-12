import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import io

st.title("Product Link Finder")

# Create scraper session
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def get_product_link(sku):
    """Search Jumia for the SKU and return product link or NONE."""
    try:
        search_url = f"https://www.jumia.co.ke/catalog/?q={sku}"
        res = scraper.get(search_url)
        if res.status_code != 200:
            return "NONE"
        soup = BeautifulSoup(res.text, "html.parser")
        product_tag = soup.select_one("a.core")
        if product_tag and "href" in product_tag.attrs:
            return "https://www.jumia.co.ke" + product_tag["href"]
        return "NONE"
    except Exception:
        return "NONE"

# Option 1: Single SKU search
sku_input = st.text_input("Enter a single Jumia SKU (optional):")

if st.button("Get Single SKU Link"):
    if sku_input.strip():
        link = get_product_link(sku_input.strip())
        if link != "NONE":
            st.success(f"Product Link: {link}")
            st.markdown(f"[{link}]({link})")
        else:
            st.error("Product not found online.")
    else:
        st.warning("Please enter a SKU.")

st.markdown("---")

# Option 2: Bulk upload
uploaded_file = st.file_uploader("Upload Excel or CSV with SKUs", type=["xlsx", "csv"])

if uploaded_file:
    # Read file
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Assume SKU column
    if "SKU" not in df.columns:
        st.error("File must have a column named 'SKU'.")
        st.stop()

    st.info(f"Found {len(df)} SKUs. Processing...")

    # Get links
    df["Product Link"] = df["SKU"].astype(str).apply(get_product_link)

    # Show table
    st.dataframe(df)

    # Download as CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv_buffer.getvalue(),
        file_name="jumia_links.csv",
        mime="text/csv"
    )
