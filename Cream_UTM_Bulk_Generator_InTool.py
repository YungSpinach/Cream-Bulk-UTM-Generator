import streamlit as st
import pandas as pd
from urllib.parse import urlencode, quote_plus

st.set_page_config(page_title="Bulk UTM Generator (In-Tool)", layout="wide")
st.image("https://images.squarespace-cdn.com/content/5c9e3048523958515c382443/2129c340-d177-48e6-8b14-3c8b01a94ec7/CreamLogo-EMAILSIGNATURE.png?content-type=image%2Fpng", width=100)
st.title("Bulk UTM Generator (In-Tool)")
st.markdown("Input your campaign data directly into the table below to generate UTM URLs.")

# --- Column Definitions ---
COLUMNS = [
    'Base_URL',
    'campaign_source',
    'campaign_medium',
    'campaign_name',
    'campaign_ID',
    'campaign_term',
    'campaign_content'
]

# --- Helper Functions ---

@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

def generate_utm_url(row):
    """Generates a single UTM campaign URL from a DataFrame row."""
    base_url = row.get('Base_URL')
    # Return empty if no base URL is provided
    if not base_url or pd.isna(base_url) or str(base_url).strip() == '':
        return ""

    # Mapping from DataFrame columns to UTM parameters
    utm_mapping = {
        'utm_source': row.get('campaign_source'),
        'utm_medium': row.get('campaign_medium'),
        'utm_name': row.get('campaign_name'),
        'utm_id': row.get('campaign_ID'),
        'utm_term': row.get('campaign_term'),
        'utm_content': row.get('campaign_content'),
    }

    # Filter out any parameters that are empty, null (NaN), or just whitespace
    active_utm_params = {k: v for k, v in utm_mapping.items() if pd.notna(v) and str(v).strip() != ''}

    # If no active UTM parameters, return the base URL as is
    if not active_utm_params:
        return base_url

    # URL-encode the parameters
    encoded_params = urlencode(active_utm_params, quote_via=quote_plus)

    # Append parameters to the base URL
    if '?' in base_url:
        return f"{base_url}&{encoded_params}"
    else:
        return f"{base_url}?{encoded_params}"

# --- Main App Logic ---

# 1. Interactive Data Input
st.header("1. Input Your Campaign Data")
st.info("Add your data in the table below. You can add more rows using the '+' button at the bottom.")

# Create an initial DataFrame with one empty row to guide the user
# When creating an empty DataFrame for the editor, pandas defaults to a 'float' dtype
# for empty columns, which is incompatible with st.column_config.TextColumn.
# To fix this, we explicitly create a DataFrame with string values (empty strings).
initial_df = pd.DataFrame([{col: "" for col in COLUMNS}])

# Use st.data_editor for interactive input
input_df = st.data_editor(
    initial_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={col: st.column_config.TextColumn(required=False) for col in COLUMNS},
    key="data_editor"
)

# 2. Generate URLs Button
st.header("2. Generate and View URLs")
if st.button("Generate Campaign URLs", type="primary"):
    # Process the data from the editor
    df = input_df.copy()

    # Filter out rows where Base_URL is completely empty or just whitespace
    df.dropna(how='all', inplace=True) # Drop rows that are entirely empty
    df = df[df['Base_URL'].notna() & (df['Base_URL'].str.strip() != '')].reset_index(drop=True)

    if df.empty:
        st.warning("Please enter at least one `Base_URL` and other parameters to generate URLs.")
    else:
        # 3. Generate URLs and Display Results
        st.subheader("Generated Campaign URLs")

        # Apply the function to each row
        df['campaign_URL'] = df.apply(generate_utm_url, axis=1)

        # Create a new column for the clickable link
        df['testing_link'] = df['campaign_URL']

        # Display the final table with clickable links
        st.info("Click the links in the 'Testing Link' column to test them.")
        st.data_editor(
            df,
            column_config={
                "campaign_URL": st.column_config.TextColumn(
                    "Campaign URL",
                    help="The full generated campaign URL."
                ),
                "testing_link": st.column_config.LinkColumn(
                    "Testing Link",
                    help="Click to open and test the generated URL in a new tab.",
                    display_text="🔗 Open Link"
                )
            },
            hide_index=True,
            use_container_width=True,
            # Make output table read-only
            disabled=COLUMNS + ['campaign_URL']
        )

        # 4. Download Results
        st.header("3. Download Your Results")
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label="Download data as CSV",
            data=csv_data,
            file_name='utm_campaign_urls.csv',
            mime='text/csv',
        )
        st.image("https://substackcdn.com/image/fetch/$s_!gulA!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fbucketeer-e05bbc84-baa3-437e-9518-adb32be77984.s3.amazonaws.com%2Fpublic%2Fimages%2F6e954df9-02a8-460d-ba90-9cea62c0ac48_500x375.jpeg", width=200)

else:
    st.info("Click the 'Generate Campaign URLs' button after entering your data.")