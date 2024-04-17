import os
import logging
import traceback
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
import sys
sys.path.append("..")
from utilities.helpers.AzureSearchHelper import AzureSearchHelper

load_dotenv()

logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Delete Data", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
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

if st.session_state["profile"]["group"] != "Orai_Admin":
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

custom_css = """
    /* Poner abajo el input text */
    .st-fj {
        max-width: 1000px;
    }
    .st-bd.st-e4.st-e3.st-f9.st-fa.st-af {
        max-width: 1000px;
    }
"""
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

def get_files():
    return search_client.search("*", select="id, title", include_total_count=True)

def output_results(results):
    files = {}
    if results.get_count() == 0:
        st.info("No files available.")
        st.stop()

    for result in results:
        id = result['id']
        filename = result['title']
        if filename in files:
            files[filename].append(id)
        else:
            files[filename] = [id]

    file_options = [f"{i + 1}. {filename}" for i, filename in enumerate(files.keys())]
    st.markdown(f"**Total number of files indexed: {len(file_options)}**")

    selected_files = st.multiselect("Files to delete", file_options, [])
    st.markdown(f"**Selected files: {len(selected_files)}**")

    files_to_delete = {filename.split(". ", 1)[1]: files[filename.split(". ", 1)[1]] for filename in selected_files}
    return files_to_delete

def delete_files(files):
    ids_to_delete = []
    files_to_delete = []

    for filename, ids in files.items():
        files_to_delete.append(filename)
        ids_to_delete += [{'id': id} for id in ids]

    if len(ids_to_delete) == 0:
        st.info("No files selected")
        st.stop()

    search_client.delete_documents(ids_to_delete)

    st.success('Deleted files: ' + str(files_to_delete))

try:
    st.title('Delete Data')
    st.markdown("This page allows you to delete data from Azure Cognitive Search. Select the files you want to delete and click the button below.")

    st.markdown("---------------------------------------")

    vector_store_helper: AzureSearchHelper = AzureSearchHelper(index_name=os.getenv("AZURE_INGEST_INDEX"))
    search_client = vector_store_helper.get_vector_store().client

    results = get_files()
    with st.spinner(text="Adding documents to delete...", cache=False):
        files = output_results(results)

    if st.button("Delete"):
        with st.spinner("Deleting files..."):
            delete_files(files)

except Exception as e:
    st.error(traceback.format_exc())