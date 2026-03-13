import streamlit as st
import pandas as pd
from urllib.parse import urlencode, quote_plus

# --- Page Config and App Title ---
st.set_page_config(page_title="Cream Bulk UTM Generator", layout="wide")
# The main title and image will be displayed on every page.
st.image("https://images.squarespace-cdn.com/content/5c9e3048523958515c382443/2129c340-d177-48e6-8b14-3c8b01a94ec7/CreamLogo-EMAILSIGNATURE.png?content-type=image%2Fpng", width=100)
st.title("Bulk Campaign URL Generator (UTMs)")
st.caption("NB: avoid using spaces and special characters (&, %, etc.) in your campaign parameters. Use dashes or underscores instead. For example, use `summer_sale` instead of `summer sale` for the `campaign_name` parameter.")
st.caption("To faciliate easy reporting (including in funnel / GA), make the UTM parameters match naming conventions in ad platform (including case sensitivity).")

# --- Column Definitions (Shared) ---
# Defining columns here for consistency across the app
COLUMNS = [
    'Base_URL',
    'campaign_source',
    'campaign_medium',
    'campaign_name',
    'campaign_ID',
    'campaign_term',
    'campaign_content'
]

# --- Shared Helper Functions ---

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

# --- Page Implementations ---

def page_excel_upload():
    """Renders the page for generating UTMs from an Excel file upload."""
    st.header("Excel Upload")
    st.markdown("---")
    
    # 1. File Uploader
    st.subheader("1. Upload Your File")
    st.markdown(
        """
        Upload an Excel file (`.xlsx`) with your base URLs and campaign parameters.
        Your file should contain columns with the following headers (case-sensitive):
        - `Base_URL`
        - `campaign_source`
        - `campaign_medium`
        - `campaign_name`
        - `campaign_ID` (Optional)
        - `campaign_term` (Optional)
        - `campaign_content` (Optional)
        """
    )

    st.markdown("---")
    st.subheader("Download Template")
    st.markdown("Don't have a file? Download the template to get started.")

    @st.cache_data
    def load_template_file(path):
        """Reads the template file from disk and returns its content as bytes."""
        with open(path, "rb") as f:
            return f.read()

    try:
        # NOTE: This requires 'input_template.xlsx' to be in the same directory
        template_file_bytes = load_template_file('input_template.xlsx')
        st.download_button(
            label="📥 Download Excel Template",
            data=template_file_bytes,
            file_name='input_template.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except FileNotFoundError:
        st.warning("`input_template.xlsx` not found in the app's directory. The template download button is disabled.")
    st.markdown("---")

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="excel_uploader")

    if uploaded_file is not None:
        try:
            try:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            except ImportError:
                st.error("ERROR: The `openpyxl` library is required to read Excel files.\n\nPlease install it in your terminal by running: `pip install openpyxl`")
                st.stop()

            st.subheader("2. Review Input Data")
            st.dataframe(df)

            if 'Base_URL' not in df.columns:
                st.error("Error: The uploaded file must contain a 'Base_URL' column.")
            else:
                st.subheader("3. Generated Campaign URLs")
                df['campaign_URL'] = df.apply(generate_utm_url, axis=1)
                df['testing_link'] = df['campaign_URL']

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
                    use_container_width=True
                )

                st.subheader("4. Download Your Results")
                csv_data = convert_df_to_csv(df)
                st.download_button(
                    label="Download data as CSV",
                    data=csv_data,
                    file_name='utm_campaign_urls.csv',
                    mime='text/csv',
                )
                st.image("https://substackcdn.com/image/fetch/$s_!gulA!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fbucketeer-e05bbc84-baa3-437e-9518-adb32be77984.s3.amazonaws.com%2Fpublic%2Fimages%2F6e954df9-02a8-460d-ba90-9cea62c0ac48_500x375.jpeg", width=200)
                st.title("All the best!")


        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")
    else:
        st.info("Awaiting file upload to generate UTM URLs.")

def page_in_tool_input():
    """Renders the page for generating UTMs from the interactive table."""
    st.header("In-Tool Input")
    st.markdown("---")
    st.markdown("Input your campaign data directly into the table below to generate UTM URLs.")

    # 1. Interactive Data Input
    st.subheader("1. Input Your Campaign Data")
    st.info("Add your data in the table below. You can add more rows using the '+' button at the bottom.")

    initial_df = pd.DataFrame([{col: "" for col in COLUMNS}])

    input_df = st.data_editor(
        initial_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={col: st.column_config.TextColumn(required=False) for col in COLUMNS},
        key="data_editor"
    )

    # 2. Generate URLs Button
    st.subheader("2. Generate and View URLs")
    if st.button("Generate Campaign URLs", type="primary"):
        df = input_df.copy()
        df.dropna(how='all', inplace=True)
        df = df[df['Base_URL'].notna() & (df['Base_URL'].str.strip() != '')].reset_index(drop=True)

        if df.empty:
            st.warning("Please enter at least one `Base_URL` and other parameters to generate URLs.")
        else:
            st.subheader("Generated Campaign URLs")
            df['campaign_URL'] = df.apply(generate_utm_url, axis=1)
            df['testing_link'] = df['campaign_URL']

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
                disabled=COLUMNS + ['campaign_URL']
            )

            st.subheader("3. Download Your Results")
            csv_data = convert_df_to_csv(df)
            st.download_button(
                label="Download data as CSV",
                data=csv_data,
                file_name='utm_campaign_urls.csv',
                mime='text/csv',
            )
            st.image("https://substackcdn.com/image/fetch/$s_!gulA!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fbucketeer-e05bbc84-baa3-437e-9518-adb32be77984.s3.amazonaws.com%2Fpublic%2Fimages%2F6e954df9-02a8-460d-ba90-9cea62c0ac48_500x375.jpeg", width=200)
            st.title("All the best!")
    else:
        st.info("Click the 'Generate Campaign URLs' button after entering your data.")

# --- Main App Navigation ---
# A dictionary to map page names to their rendering functions
PAGES = {
    "Excel Upload": page_excel_upload,
    "In-Tool Input": page_in_tool_input
}

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Get the function from the dictionary and run it
page_function = PAGES[selection]
page_function()