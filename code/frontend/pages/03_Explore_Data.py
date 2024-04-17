import os
import json
import traceback
import logging
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
import sys
sys.path.append("..")
from utilities.helpers.AzureSearchHelper import AzureSearchHelper

load_dotenv()

logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Explore Data", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
mod_page_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(mod_page_style, unsafe_allow_html=True)

hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

if  st.session_state["profile"]["group"] != "Orai_Admin":
    st.error("You are not authorized to view this page.")
    st.stop()

add_logo("images/logo_small.png", height=70)

def clear_session():
    for key in st.session_state.keys():
        del st.session_state[key]
    switch_page("home")

with st.sidebar:
    if st.button("Logout"):
        clear_session()

try:
    st.title('Explore Data')
    st.markdown("This page allows you to explore the data that has been ingested into the system. The data and the metadata are stored in a vector store (Azure AI Search). The data is stored in chunks, so you can see the content of each chunk.")
    st.markdown("---------------------------------------")

    vector_store_helper: AzureSearchHelper = AzureSearchHelper(index_name=os.getenv("AZURE_INGEST_INDEX"))
    search_client = vector_store_helper.get_vector_store().client
    results = search_client.search("*", select="id, title", include_total_count=True)

    files = {}
    if results.get_count() == 0:
        st.info("No files available.")
        st.stop()

    unique_files = list(set(result['title'] for result in results))
    selected_index = st.selectbox('Select your file:', range(1, len(unique_files) + 1), format_func=lambda x: f"{x}. {unique_files[x - 1]}" if x > 0 and x <= len(unique_files) else "")

    if 0 <= selected_index - 1 < len(unique_files):  
        if st.button(label = "Search document information", key = "chunk-button"):
            selected_filename = unique_files[selected_index - 1]
            st.markdown("---------------------------------------")
            st.markdown(f'Showing chunks for: **{selected_filename}**')
            results = search_client.search("*", select="title, content, metadata", filter=f"title eq '{selected_filename}'")
            data = [[json.loads(result['metadata'])['chunk'], result['content']] for result in results]
            df = pd.DataFrame(data, columns=('Chunk', 'Content')).sort_values(by=['Chunk'])
            st.table(df)
    else:
        st.markdown("Invalid selection.")

except Exception as e:
    st.error(traceback.format_exc())