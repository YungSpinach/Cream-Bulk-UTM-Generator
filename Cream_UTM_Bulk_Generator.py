import streamlit as st
import pandas as pd
from urllib.parse import urlencode, quote_plus

st.set_page_config(page_title="Bulk UTM Generator", layout="wide")
st.image("https://images.squarespace-cdn.com/content/5c9e3048523958515c382443/2129c340-d177-48e6-8b14-3c8b01a94ec7/CreamLogo-EMAILSIGNATURE.png?content-type=image%2Fpng", width=100)
st.text("")
st.title("Cream Bulk UTM Generator")

# --- Main App Logic ---

# 1. File Uploader
st.header("1. Upload Your File")
st.markdown(
    """
    Upload an Excel file (`.xlsx`) with your base URLs and campaign parameters.
    Your file should contain the following columns:
    - `Base URL`
    - `Campaign Source`
    - `Campaign Medium`
    - `Campaign Name`
    - `Campaign Term` (Optional)
    - `Campaign Content` (Optional)
    """
)
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

# Function to convert DataFrame to CSV for download
@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# Function to generate the UTM URL
def generate_utm_url(row):
    """Generates a single UTM campaign URL from a DataFrame row."""
    base_url = row.get('Base URL')
    # Return empty if no base URL is provided
    if not base_url or pd.isna(base_url):
        return ""

    # Mapping from DataFrame columns to UTM parameters
    utm_mapping = {
        'utm_source': row.get('Campaign Source'),
        'utm_medium': row.get('Campaign Medium'),
        'utm_name': row.get('Campaign Name'),
        'utm_term': row.get('Campaign Term'),
        'utm_content': row.get('Campaign Content'),
    }

    # Filter out any parameters that are empty or NaN
    active_utm_params = {k: v for k, v in utm_mapping.items() if pd.notna(v) and str(v).strip() != ''}

    # If no active UTM parameters, return the base URL as is
    if not active_utm_params:
        return base_url

    # URL-encode the parameters (e.g., spaces become '+')
    encoded_params = urlencode(active_utm_params, quote_via=quote_plus)

    # Append parameters to the base URL
    if '?' in base_url:
        # If '?' already exists, append with '&'
        return f"{base_url}&{encoded_params}"
    else:
        # Otherwise, start the query string with '?'
        return f"{base_url}?{encoded_params}"

if uploaded_file is not None:
    try:
        # 2. Read and Process Data
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except ImportError:
            st.error("ERROR: The `openpyxl` library is required to read Excel files.\n\nPlease install it in your terminal by running: `pip install openpyxl`")
            st.stop()

        st.header("2. Review Input Data")
        st.dataframe(df)

        # Check if the essential 'Base URL' column exists
        if 'Base URL' not in df.columns:
            st.error("Error: The uploaded file must contain a 'Base URL' column.")
        else:
            # 3. Generate URLs and Display Results
            st.header("3. Generated Campaign URLs")
            
            # Apply the function to each row to create the new 'campaign_URL' column
            df['campaign_URL'] = df.apply(generate_utm_url, axis=1)

            # Display the final table with clickable links
            st.info("Click the links in the 'Campaign URL' column to test them.")
            st.data_editor(
                df,
                column_config={
                    "campaign_URL": st.column_config.LinkColumn(
                        "Campaign URL",
                        help="Click to open and test the generated URL in a new tab.",
                        display_text="🔗 Open Link"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            # 4. Download Results
            st.header("4. Download Your Results")
            csv_data = convert_df_to_csv(df)
            st.download_button(
                label="Download data as CSV",
                data=csv_data,
                file_name='utm_campaign_urls.csv',
                mime='text/csv',
            )

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

else:
    st.info("Awaiting file upload to generate UTM URLs.")
