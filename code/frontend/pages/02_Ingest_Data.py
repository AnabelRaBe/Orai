import os
import time
import chardet
import logging
import requests
import mimetypes
import traceback
import urllib.parse
import json
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from azure.storage.blob import BlobServiceClient, generate_blob_sas, ContentSettings
import streamlit_antd_components as sac
import sys
sys.path.append("..")
from utilities.helpers.ConfigHelper import ConfigHelper

load_dotenv()

logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Ingest Data", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
mod_page_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(mod_page_style, unsafe_allow_html=True)

if st.session_state["profile"]["group"] != "Orai_Admin" and st.session_state["profile"]["group"] != "Orai_Advance":
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

config = ConfigHelper.get_active_config_or_default()

def init_ingest_data():
    if "submited_form" not in st.session_state:
            st.session_state["submited_form"] = []
    if "metadata_files" not in st.session_state:
        st.session_state["metadata_files"] = []
    if 'global_business_metadata_1' not in st.session_state:
        st.session_state['global_business_metadata_1'] = config.metadata.global_business
    if 'divisions_and_areas_metadata_1' not in st.session_state:
        st.session_state['divisions_and_areas_metadata_1'] = config.metadata.divisions_and_areas
    if 'tags_metadata_1' not in st.session_state:
        st.session_state['tags_metadata_1'] = config.metadata.tags
    if 'regions_and_countries_metadata_1' not in st.session_state:
        st.session_state['regions_and_countries_metadata_1'] = config.metadata.regions_and_countries
    if 'languages_metadata_1' not in st.session_state:
        st.session_state['languages_metadata_1'] = config.metadata.languages
    if 'years_metadata_1' not in st.session_state:
        st.session_state['years_metadata_1'] = config.metadata.years
    if 'periods_metadata_1' not in st.session_state:
        st.session_state['periods_metadata_1'] = config.metadata.periods
    if 'importances_metadata_1' not in st.session_state:
        st.session_state['importances_metadata_1'] = config.metadata.importances
    if 'securities_metadata_1' not in st.session_state:
        st.session_state['securities_metadata_1'] = config.metadata.securities
    if 'origins_metadata_1' not in st.session_state:
        st.session_state['origins_metadata_1'] = config.metadata.origins
    if 'domains_metadata_1' not in st.session_state:
        st.session_state['domains_metadata_1'] = config.metadata.domains    

    if 'answering_prompt_1' not in st.session_state:
        st.session_state['answering_prompt_1'] = config.prompts.answering_prompt
    if 'post_answering_prompt_1' not in st.session_state:
        st.session_state['post_answering_prompt_1'] = config.prompts.post_answering_prompt
    if 'enable_post_answering_prompt' not in st.session_state:
        st.session_state['enable_post_answering_prompt_1'] = config.prompts.enable_post_answering_prompt
    if 'post_answering_filter_message_1' not in st.session_state:
        st.session_state['post_answering_filter_message_1'] = config.messages.post_answering_filter
    if 'faq_answering_prompt_1' not in st.session_state:
        st.session_state['faq_answering_prompt_1'] = config.prompts.faq_answering_prompt
    if 'faq_content_1' not in st.session_state:
        st.session_state['faq_content_1'] = config.prompts.faq_content

    if 'default_questions_1' not in st.session_state:
        st.session_state['default_questions_1'] = config.default_questions

    if 'log_tokens_1' not in st.session_state:
        st.session_state['log_tokens_1'] = config.logging.log_tokens
    if 'orchestrator_strategy_1' not in st.session_state:
        st.session_state['orchestrator_strategy_1'] = config.orchestrator.strategy.value

    if 'document_processors_1' not in st.session_state:
        st.session_state['document_processors_1'] = config.document_processors_list

    if 'llm_model_1' not in st.session_state:
        st.session_state['llm_model_1'] = config.llm.model
    if 'llm_max_tokens_1' not in st.session_state:
        st.session_state['llm_max_tokens_1'] = config.llm.max_tokens
    if 'llm_temperature_1' not in st.session_state:
        st.session_state['llm_temperature_1'] = config.llm.temperature
    if 'llm_top_p_1' not in st.session_state:
        st.session_state['llm_top_p_1'] = config.llm.top_p
    if 'max_followups_questions_1' not in st.session_state:
        st.session_state['max_followups_questions_1'] = config.llm.max_followups_questions
    if 'llm_embeddings_model_1' not in st.session_state:
        st.session_state['llm_embeddings_model_1'] = config.llm_embeddings.model


def validate_answering_prompt():
    if "{sources}" not in st.session_state.answering_prompt:
        st.warning("Your answering prompt doesn't contain the variable `{sources}`")
    if "{question}" not in st.session_state.answering_prompt:
        st.warning("Your answering prompt doesn't contain the variable `{question}`")
        
def validate_post_answering_prompt():
    if "post_answering_prompt" not in st.session_state or len(st.session_state.post_answering_prompt) == 0:
        pass
    if "{sources}" not in st.session_state.post_answering_prompt:
        st.warning("Your post answering prompt doesn't contain the variable `{sources}`")
    if "{question}" not in st.session_state.post_answering_prompt:
        st.warning("Your post answering prompt doesn't contain the variable `{question}`")
    if "{answer}" not in st.session_state.post_answering_prompt:
        st.warning("Your post answering prompt doesn't contain the variable `{answer}`")

def remote_convert_files_and_add_embeddings(index_name: str, process_all: bool = False):
    backend_url = urllib.parse.urljoin(os.getenv('BACKEND_URL','http://localhost:7071'), "/api/BatchStartProcessing")
    
    params = {"process_all": "false",
              "index_name": index_name,
              "metadata": st.session_state["metadata_files"],
              "container_name": os.getenv('AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME'),
              }
    
    if os.getenv('FUNCTION_KEY') != None:
        params['clientKey'] = os.getenv('FUNCTION_KEY')
    if process_all:
        params['process_all'] = "true"
    try:
        response = requests.post(backend_url, json=params)
        if response.status_code == 200:
            st.success(f"{response.text}\nEmbeddings computation in progress. \nPlease note this is an asynchronous process and may take a few minutes to complete.\nYou can check for further details in the Azure Function logs.")
        else:
            st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(traceback.format_exc())

def upload_file(bytes_data: bytes, file_name: str, content_type: Optional[str] = None):    
    st.session_state['filename'] = file_name
    if content_type == None:
        content_type = mimetypes.MimeTypes().guess_type(file_name)[0]
        charset = f"; charset={chardet.detect(bytes_data)['encoding']}" if content_type == 'text/plain' else ''
        content_type = content_type if content_type != None else 'text/plain'
    account_name = os.getenv('AZURE_BLOB_ACCOUNT_NAME')
    account_key =  os.getenv('AZURE_BLOB_ACCOUNT_KEY')
    container_name = os.getenv('AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME')
    if account_name == None or account_key == None or container_name == None:
        raise ValueError("Please provide values for AZURE_BLOB_ACCOUNT_NAME, AZURE_BLOB_ACCOUNT_KEY and AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME")
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    blob_service_client : BlobServiceClient = BlobServiceClient.from_connection_string(connect_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type+charset))
    st.session_state['file_url'] = blob_client.url + '?' + generate_blob_sas(account_name, container_name, file_name,account_key=account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))

def join_regions_countries():
    region_country_list = []

    for region, countries in st.session_state['regions_and_countries_metadata_1'].items():
        if countries == []:
            region_country_list.append(f"{region}")
        else:
            for country in countries:
                region_country_list.append(f"{region}-{country}")
        
    return region_country_list

def save_configuration():
    current_config = {
        "welcome_message": config.welcome_message,
        "default_questions": st.session_state['default_questions_1'],
        "prompts": {
            "condense_question_prompt": "",
            "answering_prompt": st.session_state['answering_prompt_1'],
            "post_answering_prompt": st.session_state['post_answering_prompt_1'],
            "enable_post_answering_prompt": st.session_state['enable_post_answering_prompt_1'],
            "faq_answering_prompt": st.session_state['faq_answering_prompt_1'],
            "faq_content": st.session_state['faq_content_1'],
        },
        "messages": {
            "post_answering_filter": st.session_state['post_answering_filter_message_1']
        },
        "document_processors":  st.session_state['document_processors_1'],
        "logging": {
            "log_tokens": st.session_state['log_tokens_1']
        },
        "orchestrator": {
            "strategy": st.session_state['orchestrator_strategy_1']
        },
        "llm": {
            "model": st.session_state['llm_model_1'],
            "max_tokens": st.session_state['llm_max_tokens_1'],
            "temperature": st.session_state['llm_temperature_1'],
            "top_p": st.session_state['llm_top_p_1'],
            "max_followups_questions": st.session_state['max_followups_questions_1']
        },
        "llm_embeddings": {
            "model": st.session_state['llm_embeddings_model_1']
        },
        "metadata": {
            "global_business": st.session_state['global_business_metadata_1'],
            "divisions_and_areas": st.session_state['divisions_and_areas_metadata_1'],
            "tags": st.session_state['tags_metadata_1'],
            "regions_and_countries": st.session_state['regions_and_countries_metadata_1'],
            "languages": st.session_state['languages_metadata_1'],
            "years": st.session_state['years_metadata_1'],
            "periods": st.session_state['periods_metadata_1'],
            "importances": st.session_state['importances_metadata_1'],
            "securities": st.session_state['securities_metadata_1'],
            "origins": st.session_state['origins_metadata_1'],
            "domains": st.session_state['domains_metadata_1']
        }
    }
    ConfigHelper.save_config_as_active(current_config)
    st.success("Configuration saved successfully!")


try:

    init_ingest_data()    

    st.title('Ingest Data')
    st.markdown("This page allows you to ingest data into the system. Each document will be processed by the document processors configured in the configuration file. Then, chunk embeddings will be computed and added to the Azure Cognitive Search index.")
    sac.alert(label='Prior to uploading the document, it is imperative to consider various ingest strategies:', description='- Layout: This entails uploading documentation that will be segmented on a per-page basis. Consequently, all information contained on each page will be acquired in its entirety. **Recommended for documents with < 100 pages**. \n - Page: This involves the upload of documentation segmented by page, with the additional subdivision of information on each page into smaller units, known as chunks. Two key parameters must be taken into consideration for this strategy: Chunk size (denoting the amount of information desired for each chunk) and Chunk overlap (indicating the amount of information to be retained between two chunks to mitigate potential information loss). **Recommended for documents with > 100 pages**.  <br><br> When determining the appropriate option, the default recommendation is to opt for the layout strategy to optimize knowledge acquisition and circumvent potential disruptions in the presentation of tables, diagrams, etc., as long as the document intended for upload under this strategy does not surpass approximately 150 pages. This limitation is attributable to Azure OpenAI quota restrictions. For documents exceeding this page threshold > 100, the "Page" type chunking strategy becomes necessary. <br><br> It will depend on the complexity of the documents. If it is a non-enriched document, which does not contain graphics, tables, etc., only plain text, the layout strategy could be used for documents with a larger number of pages between 100-200 pages. <br><br> Please note this is an asynchronous process and may take a few minutes to complete. You can check for further details in the Azure Function logs.',
               size='sm', color='warning', icon=True, closable=True)
    st.markdown("---------------------------------------")
    config = ConfigHelper.get_active_config_or_default()
    with st.expander("Attach file:", expanded=True):
        file_type = [processor.document_type for processor in config.document_processors]
        uploaded_files = st.file_uploader("Upload a document to add it to the Azure Storage Account, compute embeddings and add them to the Azure Cognitive Search index. Check your configuration for available document processors.", type=file_type, accept_multiple_files=True)
        if uploaded_files is not None:
            for up in uploaded_files:
                bytes_data = up.getvalue()
                if st.session_state.get('filename', '') != up.name:
                    upload_file(bytes_data, up.name)
            if len(uploaded_files) > 0:
                st.success(f"{len(uploaded_files)} documents uploaded.")

        for file in uploaded_files:
            clave = file.name
            dict_file = {}

            with st.form(key=f"metadata_form_{file.name}"):
                st.markdown(f"**{file.name}**")

                global_business = st.selectbox("Global business options", st.session_state['global_business_metadata_1'])
                divisions_and_areas = st.selectbox("Divisions and areas options", st.session_state['divisions_and_areas_metadata_1'])

                tags_selected = st.multiselect("Tags options", st.session_state['tags_metadata_1'], [], placeholder = "Choose one or more tags...")
                tags_written = st_tags(
                    label = "Write your own tags just in English:",
                    text='Press enter to add more',
                    value=[],
                    maxtags = 4,
                    key=f'tags-file-{file.name}')

                tags = tags_selected 

                for tag in tags_written:
                    tag = tag.capitalize()
                    if tag not in tags_selected:
                        tags = tags + [tag]
                    if tag not in st.session_state['tags_metadata_1']:
                        st.session_state['tags_metadata_1'].append(tag)

                regions_and_countries = st.selectbox("Regions and countries options", join_regions_countries())
                if "-" in regions_and_countries:
                    region, country = regions_and_countries.split("-")
                else:
                    region = regions_and_countries
                    country = regions_and_countries
                
                language = st.selectbox("Language options", st.session_state['languages_metadata_1'])
                year = st.selectbox("Year options", st.session_state['years_metadata_1'])
                period = st.selectbox("Period options", st.session_state['periods_metadata_1'])
                importance = len(st.selectbox("Importance options", st.session_state['importances_metadata_1']))
                security = st.selectbox("Security options", st.session_state['securities_metadata_1'])
                origin = st.selectbox("Origin options", st.session_state['origins_metadata_1'])
                domain = st.selectbox("Domain options", st.session_state['domains_metadata_1'])
                
                if st.form_submit_button(disabled=False): 
                    if file not in st.session_state["submited_form"]:
                        st.session_state["submited_form"].append(file) 

                    value = {
                        "global_business": global_business,
                        "divisions_and_areas": divisions_and_areas,
                        "tags": tags,
                        "region": region,
                        "country": country,
                        "language": language,
                        "year": year,
                        "period": period,
                        "importance": importance,
                        "security": security,
                        "origin": origin,
                        "domain": domain
                    }

                    for file in st.session_state["metadata_files"]:
                        keys = list(file.keys())

                        if keys[0] == clave:
                            st.session_state["metadata_files"].remove(file)
                        
                    dict_file[clave] = value
                    st.session_state["metadata_files"].append(dict_file)

                    save_configuration()
                
                if file in st.session_state["submited_form"]:
                    response_success_button = st.success(f"This file has been submited: {file.name}")
                    time.sleep(3)
                    response_success_button.empty()
                
        for form in st.session_state["submited_form"]:
            if form not in uploaded_files:
                st.session_state["submited_form"].remove(form)

        if (len(st.session_state["submited_form"]) == len(uploaded_files)) and (len(uploaded_files) >0 ):
            disabled_process_button = False
        else:
            disabled_process_button = True
        
        if st.button("Process uploaded documents in the Azure Storage account", on_click=remote_convert_files_and_add_embeddings, args=(os.getenv("AZURE_INGEST_INDEX"), False,), disabled=disabled_process_button):
            st.session_state["submited_form"] = []
            st.session_state["metadata_files"] = []
            

    document_processors = list(map(lambda x: {
        "document_type": x.document_type, 
        "chunking_strategy": x.chunking.chunking_strategy.value, 
        "chunking_size": x.chunking.chunk_size,
        "chunking_overlap": x.chunking.chunk_overlap, 
        "loading_strategy": x.loading.loading_strategy.value,
        }, config.document_processors))

    with st.expander("The current configuration for document processing is:", expanded=True):
        edited_document_processors = st.data_editor(
            data= document_processors,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "document_type": st.column_config.SelectboxColumn( 
                    options= config.get_available_document_types()
                ),
                "chunking_strategy": st.column_config.SelectboxColumn(
                    options=[cs for cs in config.get_available_chunking_strategies()]
                ),
                "loading_strategy": st.column_config.SelectboxColumn(
                    options=[ls for ls in config.get_available_loading_strategies()]
                )
            }         
         )
        
    if st.button("Save configuration"):
        document_processors = list(map(lambda x: {
            "document_type": x["document_type"],
            "chunking": {
                "strategy": x["chunking_strategy"],
                "size": x["chunking_size"],
                "overlap": x["chunking_overlap"]
            },
            "loading": {
                "strategy": x["loading_strategy"],
            }
            }, edited_document_processors))
        
        st.session_state['document_processors_1'] = document_processors

        save_configuration()

except Exception as e:
    st.error(traceback.format_exc()) 