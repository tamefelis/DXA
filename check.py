import streamlit as st
import pandas as pd
import logging
import os
from logging.handlers import RotatingFileHandler

# Set up a rotating file handler
log_file = 'concise_data_screening_log.txt'
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=2, delay=True)

# Configure logging format
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)

# Add handler to the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)


def check_dexa_data(uploaded_file):
    # Read the CSV file directly from the uploaded file object
    df = pd.read_csv(uploaded_file)

    # Define metadata and DEXA parameter columns
    metadata_cols = ['DXA_subjID', 'DXA_subVisit', 'DXA_date#1_1', 'DXA_date#2_1', 'DXA_date#3_1']
    dexa_params = [col for col in df.columns if col.startswith('DXA_') and col not in metadata_cols]

    # Find duplicate metadata records
    duplicates = df.duplicated(subset=metadata_cols, keep=False)

    # Filter for only duplicate records
    dup_df = df[duplicates]

    logged_discrepancies = set()  # To keep track of logged discrepancies
    discrepancies = {}  # To accumulate discrepancies

    # Group by metadata and compare each group
    for _, group in dup_df.groupby(metadata_cols):
        if group.shape[0] == 2:  # Ensuring exactly two entries
            row1, row2 = group.iloc[0], group.iloc[1]
            for param in dexa_params:
                discrepancy_key = (row1["DXA_subjID"], row1["DXA_subVisit"], param)
                if row1[param] != row2[param] and discrepancy_key not in logged_discrepancies:
                    subj_id = row1["DXA_subjID"]
                    visit = row1["DXA_subVisit"]
                    date = f"{row1['DXA_date#1_1']} {row1['DXA_date#2_1']}, {row1['DXA_date#3_1']}"

                    if (subj_id, visit) not in discrepancies:
                        discrepancies[(subj_id, visit)] = []
                    discrepancies[(subj_id, visit)].append((date, param, row1[param], row2[param]))

                    logged_discrepancies.add(discrepancy_key)

    # Log accumulated discrepancies
    for (subj_id, visit), records in discrepancies.items():
        for record in records:
            date, param, val1, val2 = record
            logging.info(f"Subject '{subj_id}', Visit '{visit}', Date '{date}': Discrepancy in '{param}' (Record 1: {val1}, Record 2: {val2})")


# Streamlit GUI layout
st.title('DEXA Data Screening Application')

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    # Call the data screening function with the uploaded file object
    check_dexa_data(uploaded_file)


    # Display success message
    st.success('Data screening completed. Check log for details.')

    # Streamlit download button section
    if os.path.exists(log_file):
        st.subheader('Concise Log Contents:')
        with open(log_file, 'r') as file:
            log_content = file.read()
            st.text_area('Log', log_content, height=300)        

        # Write to buffer and download
        with open(log_file, 'rb') as file:
            st.download_button(
                label="Download Concise Log File",
                data=file,
                file_name=log_file,
                mime='text/plain'
            )