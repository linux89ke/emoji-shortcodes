import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import time

# Function to get Jumia product link from SKU
def get_jumia_link(sku):
    try:
        search_url = f"https://www.jumia.co.ke/catalog/?q={sku}"
        scraper = cloudscraper.create_scraper()
        response = scraper.get(search_url)

        if response.status_code != 200:
            return "NONE"

        soup = BeautifulSoup(response.text, "html.parser")
        product_tag = soup.find("a", {"class": "core"})

        if product_tag and product_tag.get("href"):
            return "https://www.jumia.co.ke" + product_tag["href"]
        else:
            return "NONE"
    except:
        return "NONE"


st.title("Jumia SKU to Product Link Finder")

# Option 1: Manual SKU input
sku_input = st.text_input("Enter a SKU to search for:")
if st.button("Find Link") and sku_input:
    with st.spinner("Searching..."):
        link = get_jumia_link(sku_input)
    st.write(f"**Result:** {link}")

# Option 2: File upload
uploaded_file = st.file_uploader("Upload Excel or CSV file with SKUs", type=["xlsx", "csv"])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    if "SKU" not in df.columns:
        st.error("Uploaded file must have a column named 'SKU'.")
    else:
        df["Link"] = ""  # Create an empty column for links
        progress_bar = st.progress(0)
        result_table = st.empty()

        for idx, sku in enumerate(df["SKU"]):
            df.at[idx, "Link"] = get_jumia_link(sku)
            progress = (idx + 1) / len(df)
            progress_bar.progress(progress)
            result_table.dataframe(df)  # Update table live
            time.sleep(0.2)  # Small delay to visualize progress

        st.success("Processing complete!")
        st.dataframe(df)

        # Download results
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="jumia_links.csv",
            mime="text/csv",
        )
