import os
import base64
import time
import json
import uuid
import chardet
import logging
import requests
import traceback
import mimetypes
import regex as re
import urllib.parse
import streamlit as st
import streamlit_antd_components as sac
from os import remove
from typing import Tuple
from random import randint
from dotenv import load_dotenv
from streamlit_chat import message
from azure.storage.blob import BlobServiceClient
from streamlit_feedback import streamlit_feedback
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from st_pages import Page, show_pages
from azure.storage.blob import BlobServiceClient, generate_blob_sas, ContentSettings
from datetime import datetime, timedelta
from typing import Optional
import sys
sys.path.append("..")
from utilities.helpers.ConfigHelper import ConfigHelper
from utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient
from utilities.tools.GenerateTopicTool import GenerateTopicTool
from utilities.helpers.OrchestratorHelper import Orchestrator

load_dotenv()

logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Chat", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
mod_page_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(mod_page_style, unsafe_allow_html=True)

def clear_session():
    for key in st.session_state.keys():
        del st.session_state[key]
    switch_page("home")

with st.sidebar:
    if st.button("Logout"):
        clear_session()
    language = st.selectbox(":speaking_head_in_silhouette: Response language",["🇪🇸  Spanish","🇬🇧  English", "🇵🇹  Portuguese","🇵🇱  Polish"])
    sep = language.split("  ")
    language = sep[1]

add_logo("images/logo_small.png", height=70)

show_pages(
    [
        Page("Home.py", "Home", "🏠"),
        Page("pages/01_Chat.py", "Chat", "🗨️"),
        Page("pages/02_Ingest_Data.py", "Ingest Data", "📁"),
        Page("pages/03_Explore_Data.py", "Explore Data", "📖"),
        Page("pages/04_Delete_Data.py", "Delete Data", "❌"),
        Page("pages/05_Metrics.py", "Metrics", "📊"),
        Page("pages/06_Configuration.py", "Configuration", "⚙️"),
    ]
)

def remote_convert_files_and_add_embeddings(files_names: list, index_name: str, process_all: bool = False):
    backend_url = urllib.parse.urljoin(os.getenv('BACKEND_URL','http://localhost:7071'), "/api/BatchStartProcessing")

    metadata = [
        {
            filename:{
                "global_business":"",
                "divisions_and_areas":"",
                "tags":[
                    
                ],
                "region":"",
                "country":"",
                "language":"",
                "year":2024,
                "period":"",
                "importance":5,
                "security":"",
                "origin":"",
                "domain":""
            }
        }
        for filename in files_names
        ]
    
    params = {"process_all": "false",
              "index_name": index_name,
              "metadata": metadata,
              "container_name": os.getenv('AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME'),
              }
    
    print("PARAMS")
    print(params)

    if process_all:
        params['process_all'] = "true"

    try:
        response = requests.post(backend_url, json=params)
        if response.status_code == 200:
            response_success_button = st.success("Documents uploaded to storage. Please note this is an asynchronous process and may take a few minutes to complete. You can check for further details in the Azure Function logs.")
            time.sleep(5)
            response_success_button.empty()
        else:
            response_error_message = st.error(f"Error: {response.text}")
            time.sleep(5)
            response_error_message.empty()
    except Exception as e:
        st.error(traceback.format_exc())

def embeddings_generation(files_names: list, user_id: str, process_all: bool = False):
    backend_url = urllib.parse.urljoin(os.getenv('BACKEND_URL','http://localhost:7071'), "/api/BatchStartProcessing")

    metadata = [
        {
            filename:{
                "global_business":"",
                "divisions_and_areas":"",
                "tags":[
                    
                ],
                "region":"",
                "country":"",
                "language":"",
                "year":2024,
                "period":"",
                "importance":5,
                "security":"",
                "origin":"",
                "domain":""
            }
        }
        for filename in files_names
        ]
    
    print("METADATOS")
    print(type(metadata))
    
    params = {
        "process_all": False,
        "user_id": user_id,
        "metadata": metadata,
        "is_global_index" : False
    }


    if process_all:
        params['process_all'] = True

    try:
        response = requests.post(backend_url, json=params)
        if response.status_code == 200:
            response_success_button = st.success("Finish embedding.")
            time.sleep(5)
            response_success_button.empty()
        else:
            response_error_message = st.error(f"Error: {response.text}")
            time.sleep(5)
            response_error_message.empty()
    except Exception as e:
        st.error(traceback.format_exc())


def handle_message(chat_history: dict,language: str, user_index_name: str) -> dict:
    orquestrator_url = urllib.parse.urljoin(os.getenv('BACKEND_URL', 'http://localhost:7072'), "/api/ConversationOrquestrator")
    
    params = {"chat_history": chat_history,
              "language":language,
              "user_index_name": user_index_name}

    try:
        response = requests.post(orquestrator_url, json=params)
        return json.loads(response.text)
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
    container_name = os.getenv('AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME')
    if account_name == None or account_key == None or container_name == None:
        raise ValueError("Please provide values for AZURE_BLOB_ACCOUNT_NAME, AZURE_BLOB_ACCOUNT_KEY and AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME")
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    blob_service_client : BlobServiceClient = BlobServiceClient.from_connection_string(connect_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type+charset))
    file_bytes_base64 = base64.b64encode(bytes_data).decode('utf-8')
    json_example = {
            "user_id" : "1234",
            "file_name" : "test.pdf",
            "file_bytes" : file_bytes_base64,
            "is_global_index" : True
        }
    print("Ejemplo:", json_example)
    st.session_state['file_url'] = blob_client.url + '?' + generate_blob_sas(account_name, container_name, file_name,account_key=account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))


def extract_followupquestions(answer: str) -> Tuple[str, list]:
    followupTag = answer.find('Follow-up Questions')
    followupQuestions = answer.find('<<')

    followupTag = min(followupTag, followupQuestions) if followupTag != -1 and followupQuestions != -1 else max(followupTag, followupQuestions)
    answer_without_followupquestions = answer[:followupTag] if followupTag != -1 else answer
    followup_questions = answer[followupTag:].strip() if followupTag != -1 else ''

    pattern = r'\<\<(.*?)\>\>'
    match = re.search(pattern, followup_questions)
    followup_questions_list = []
    while match:
        followup_questions_list.append(followup_questions[match.start()+2:match.end()-2])
        followup_questions = followup_questions[match.end():]
        match = re.search(pattern, followup_questions)
    
    if followup_questions_list != '':
        pattern = r'\d. (.*)'
        match = re.search(pattern, followup_questions)
        while match:
            followup_questions_list.append(followup_questions[match.start()+3:match.end()])
            followup_questions = followup_questions[match.end():]
            match = re.search(pattern, followup_questions)

    if followup_questions_list != '':
        pattern = r'Follow-up Question: (.*)'
        match = re.search(pattern, followup_questions)
        while match:
            followup_questions_list.append(followup_questions[match.start()+19:match.end()])
            followup_questions = followup_questions[match.end():]
            match = re.search(pattern, followup_questions)
    
    followupTag = answer_without_followupquestions.lower().find('follow-up questions')
    if followupTag != -1:
        answer_without_followupquestions = answer_without_followupquestions[:followupTag]
    followupTag = answer_without_followupquestions.lower().find('follow up questions')
    if followupTag != -1:
        answer_without_followupquestions = answer_without_followupquestions[:followupTag]

    return answer_without_followupquestions, followup_questions_list


def insert_citations_in_answer(answer: str, filenameList: list) -> Tuple[str, list, list]:
    filenameList_lowered = [x.lower() for x in filenameList]

    matched_sources = []
    pattern = r'\[\[(.*?)\]\]'
    match = re.search(pattern, answer)
    while match:
        filename = match.group(1).split('.')[0] 
        if filename in filenameList:
            if filename not in matched_sources:
                matched_sources.append(filename.lower())
            filenameIndex = filenameList.index(filename) + 1
            answer = answer[:match.start()] + '$^{' + f'{filenameIndex}' + '}$' + answer[match.end():]
        else:
            answer = answer[:match.start()] + '$^{' + f'{filename.lower()}' + '}$' + answer[match.end():]
        match = re.search(pattern, answer)

    for id, filename in enumerate(filenameList_lowered):
        reference = '$^{' + f'{id+1}' + '}$'
        if reference in answer and not filename in matched_sources:
            matched_sources.append(filename)

    return answer, matched_sources, filenameList_lowered


def date_format(json_bytes: bytes) -> str:
    date_chain = json.loads(json_bytes)["modified_date"]
    date_separated = date_chain.split("_")
 
    day = date_separated[0]
    day_list = day.split("-")
    day_final = "-".join([day_list[2], day_list[1], day_list[0]])
 
    hour = date_separated[1]
    hour_format = hour.replace("-", ":")
    hour_final = hour_format.replace("/", "")
 
    date = " ".join([day_final, hour_final])
    return date


def clear_chat_data(generate_json: bool, language: str):
    if generate_json:
        generate_json_historical(language)
    st.session_state['collected_historical_conversation'] = False
    st.session_state['chat_history'] = []
    st.session_state['chat_history_langchain'] = { "messages": [], "conversation_id": "" }
    st.session_state['chat_source_documents'] = []
    st.session_state['chat_source_document_preview'] = []
    st.session_state['chat_askedquestion'] = ''
    st.session_state['chat_question'] = ''
    st.session_state['chat_followup_questions'] = []
    st.session_state['conversation_id'] = ''
    st.session_state['conversation_init_date'] = ''
    st.session_state['conversation_file_name'] = ''
    st.session_state["file_uploader_key"] = 0
    st.session_state["uploaded_files"] = []
    st.session_state['init_chat_history'] = []
    st.session_state["conversation_topic"] = ""
    st.session_state["conversation_sources_url"] = []


def upload_session_state_variables(json_bytes: bytes, file: str):
    st.session_state['collected_historical_conversation'] = True
    st.session_state['conversation_file_name'] = file                
    st.session_state['conversation_init_date'] = json.loads(json_bytes)["init_date"]
    st.session_state['chat_history_langchain'] = json.loads(json_bytes)["langchain"] 
    st.session_state['chat_history'] = json.loads(json_bytes)["history"]
    st.session_state['chat_source_documents'] = json.loads(json_bytes)["documents"]
    st.session_state['chat_source_document_preview'] = json.loads(json_bytes)["document_preview"]
    st.session_state['chat_askedquestion'] = json.loads(json_bytes)["askedquestion"]
    st.session_state['chat_question'] = json.loads(json_bytes)["chat_question"]
    st.session_state['chat_followup_questions'] = json.loads(json_bytes)["followup_questions"]
    st.session_state['conversation_id'] = json.loads(json_bytes)["conversation_id"]
    st.session_state['input_message_key'] = json.loads(json_bytes)["input_message_key"]
    st.session_state['init_chat_history'] = json.loads(json_bytes)["history"]
    st.session_state["conversation_topic"] = json.loads(json_bytes)["topic"]
    st.session_state["conversation_sources_url"] = json.loads(json_bytes)["sources_url"]


def delete_followup_questions_txt(conversation: str) -> str:
    pattern = re.compile(r'<<.*?>>')
    result = pattern.sub('', conversation)
    
    return result


def prepare_conversation_txt(json_bytes: bytes) -> str:
    conversation = ""
    conversation += f"Last date: {date_format(json_bytes)}\n\n"
    conversation += f"\n----------------------------------------------------------------------------\n"
    conversation += f"{json.loads(json_bytes)['topic']}"
    conversation += f"\n----------------------------------------------------------------------------\n\n"

    conversation += "\n......................................\nConversation\n......................................\n\n"
    for message in json.loads(json_bytes)["langchain"]["messages"]:
        if message["role"] in ["user", "assistant"]:
            conversation += f"{message['role'].capitalize()}: {message['content']}\n\n"

    conversation = delete_followup_questions_txt(conversation)

    return conversation


def conversation_in_sidebar():
    azure_blob_client = AzureBlobStorageClient(account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME"), account_key = os.getenv("AZURE_BLOB_ACCOUNT_KEY"), container_name = os.getenv("AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME"))

    files_stored = azure_blob_client.get_all_files_by_user_id(user_id)
    files_stored_chronological = files_stored[::-1]

    with st.sidebar:
        with st.expander('**Historical conversations**'):
            i = 0
            for file in files_stored_chronological:
                json_bytes = azure_blob_client.download_file(file)
                label = json.loads(json_bytes)["topic"]
                   
                sac.divider(label=date_format(json_bytes), icon='', align='center',key=f"divider-conversation-{str(i)}-{file}")
                if st.button(label, key=f"button-conversation-{str(i)}-{file}", type="primary"):
                    upload_session_state_variables(json_bytes, file)
                    st.markdown(":pushpin: Pinned")
                
                if st.button(f":wastebasket:", key=f"button-delete-conversation-{str(i)}-{file}"):
                    if st.session_state['conversation_file_name'] == file:
                        clear_chat_data(False, language)
                    azure_blob_client.delete_file(file)
                    switch_page("Chat")    

                if st.button(f"✏️", key=f"button-edit-conversation-{str(i)}-{file}"):
                    # new_topic = st.text_input(label="Edit the topic:",value="", max_chars=20, key=f"input-edit-topic-conversation-{str(i)}-{file}", type="default", placeholder="Edit the topic", disabled=False, label_visibility="visible")
                    # edit_topic(file, json_bytes, new_topic)
                    pass
                
                st.download_button(f":arrow_down_small:", data=prepare_conversation_txt(json_bytes), key=f"button-download-conversation-{str(i)}-{file}", file_name=f"{label}.txt")                    

                i += 1


def question_asked():
    st.session_state.chat_askedquestion = st.session_state["input"+str(st.session_state ['input_message_key'])]
    st.session_state["input"+str(st.session_state ['input_message_key'])] = ""
    st.session_state.chat_question = st.session_state.chat_askedquestion


def ask_followup_question(followup_question: str):
    st.session_state.chat_askedquestion = followup_question
    st.session_state['input_message_key'] = st.session_state['input_message_key'] + 1


def add_hyperlinks(answer_without_followup: str, references: list) -> str:
    urls = [source["url"] for source in references]
    regex = r'\[([^]]+)\]'
    results = re.findall(regex, answer_without_followup)
    references_ids = [re.findall("\d+", value)[0] for value in results]
    links = [urls[int(id)-1] for id in references_ids]

    container_name = os.environ.get('AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME', 'documents2')
    for i, link in enumerate(links):
        modified_link = re.sub(f'/{re.escape(container_name)}/', '', link, count=1)
        answer_without_followup = answer_without_followup.replace(results[i], f"{modified_link}")

    return answer_without_followup


def init_chat_history():
    if 'chat_question' not in st.session_state:
        st.session_state['chat_question'] = ''
    if 'chat_askedquestion' not in st.session_state:
        st.session_state.chat_askedquestion = ''
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'chat_history_langchain' not in st.session_state:
        st.session_state['chat_history_langchain'] = { "messages": [], "conversation_id": "" }
    if 'chat_source_documents' not in st.session_state:
        st.session_state['chat_source_documents'] = []
    if 'chat_source_document_preview' not in st.session_state:
        st.session_state['chat_source_document_preview'] = []
    if 'chat_followup_questions' not in st.session_state:
        st.session_state['chat_followup_questions'] = []
    if 'input_message_key' not in st.session_state:
        st.session_state['input_message_key'] = 1
    if 'conversation_id' not in st.session_state:
        st.session_state['conversation_id'] = '' 
    if 'collected_historical_conversation' not in st.session_state:
        st.session_state['collected_historical_conversation'] = False
    if 'conversation_init_date' not in st.session_state:
        st.session_state['conversation_init_date'] = ''
    if 'conversation_file_name' not in st.session_state:
        st.session_state['conversation_file_name'] = ''
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    if 'init_chat_history' not in st.session_state:
        st.session_state['init_chat_history'] = []
    if "conversation_topic" not in st.session_state:
        st.session_state["conversation_topic"] = ""
    if "conversation_sources_url" not in st.session_state:
        st.session_state["conversation_sources_url"] = []


def prepare_blob(data_json: str, container: str, blob_name: str):
    now = datetime.now()

    parent_folder_name = user_id
    subfolder_name = now.strftime("%Y-%m-%d_%H-%M-%S")

    parent_folder_blob_name = parent_folder_name + '/'
    subfolder_blob_name = parent_folder_blob_name + subfolder_name + '/'

    file_path = f"{blob_name}"
    file_blob_name = subfolder_blob_name + file_path

    with open(file_path, "w") as json_file:
        json_file.write(data_json)

    upload_json_to_azure_storage_account(os.getenv("AZURE_BLOB_ACCOUNT_NAME"), os.getenv("AZURE_BLOB_ACCOUNT_KEY"), container, file_blob_name, file_path)

    remove(file_path)


def edit_topic(file: str, json_bytes: bytes, new_topic: str):
    now = datetime.now()

    azure_blob_client = AzureBlobStorageClient(account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME"), account_key = os.getenv("AZURE_BLOB_ACCOUNT_KEY"), container_name = os.getenv("AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME"))

    data = {
        "user_id": user_id,
        "init_date": json.loads(json_bytes)["init_date"],
        "topic": new_topic,
        "modified_date": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "langchain": json.loads(json_bytes)["langchain"],
        "history": json.loads(json_bytes)["history"],
        "documents": json.loads(json_bytes)["documents"],
        "document_preview": json.loads(json_bytes)["document_preview"],
        "sources_url": json.loads(json_bytes)["sources_url"],
        "askedquestion": json.loads(json_bytes)["askedquestion"],
        "chat_question": json.loads(json_bytes)["chat_question"],
        "followup_questions": json.loads(json_bytes)["followup_questions"],
        "conversation_id": json.loads(json_bytes)["conversation_id"],
        "input_message_key": json.loads(json_bytes)["input_message_key"]
    }
    data_json = json.dumps(data, indent=2)
    blob_name = now.strftime("conversation_%Y-%m-%d_%H-%M-%S")

    azure_blob_client.delete_file(file)

    prepare_blob(data_json, os.getenv("AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME"), blob_name)
    
    switch_page("Chat")


def generate_json_feedback(feedback: dict, question: str, answer: str, citations: list, conversation_id: str, config_LLM: dict, prompt: str):
    now = datetime.now()

    data = {
        "user_id": user_id,
        "name": st.session_state['profile']['name'],
        "date": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "conversation_id": conversation_id,
        "feedback": feedback,
        "question": question,
        "prompt": prompt,
        "answer": answer,
        "citations": citations,
        "format_feedback": {"messages": [{"role": "system", "content": answer }, {"role": "user", "content": question}]},
        "model_configuration": config_LLM 
    }
    
    data_json = json.dumps(data, indent=2)
    blob_name = now.strftime("%Y-%m-%d_%H-%M-%S_feedback_" + conversation_id)

    prepare_blob(data_json, os.getenv("AZURE_BLOB_CONTAINER_FEEDBACK_NAME"), blob_name)


def generate_json_historical(language: str):
    azure_blob_client = AzureBlobStorageClient(account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME"), account_key = os.getenv("AZURE_BLOB_ACCOUNT_KEY"), container_name = os.getenv("AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME"))
    generate_topic_tools = GenerateTopicTool()
    now = datetime.now()

    if st.session_state['collected_historical_conversation']:
        print("VOY A BORRAR")
        azure_blob_client.delete_file(st.session_state['conversation_file_name'])
        st.session_state['collected_historical_conversation'] = False
        date = st.session_state['conversation_init_date']
    else: 
        date = now.strftime("%Y-%m-%d_%H-%M-%S")

    if st.session_state["conversation_topic"] == "":
        topic = generate_topic_tools.generate_topic(st.session_state['chat_history'], language)
    else:
        topic = st.session_state["conversation_topic"]

    data = {
        "user_id": user_id,
        "init_date": date,
        "topic": topic,
        "modified_date": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "langchain": st.session_state['chat_history_langchain'],
        "history": st.session_state['chat_history'],
        "documents": st.session_state['chat_source_documents'],
        "document_preview": st.session_state['chat_source_document_preview'],
        "sources_url": st.session_state["conversation_sources_url"],
        "askedquestion": st.session_state['chat_askedquestion'],
        "chat_question": st.session_state['chat_question'],
        "followup_questions": st.session_state['chat_followup_questions'],
        "conversation_id": st.session_state ['conversation_id'],
        "input_message_key": st.session_state['input_message_key']
    }
    data_json = json.dumps(data, indent=2)
    blob_name = now.strftime(f"conversation_%Y-%m-%d_%H-%M-%S")
    prepare_blob(data_json, os.getenv("AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME"), blob_name)


def upload_json_to_azure_storage_account(storage_account_name: str, storage_account_key: str, container_name: str, file_blob_name: str, file_path: str):
    blob_service_client = BlobServiceClient(account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=storage_account_key)

    container_client = blob_service_client.get_container_client(container_name)

    blob_client = container_client.get_blob_client(file_blob_name + ".json")
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)


custom_css = """
    /* Poner abajo el input text */
    .st-emotion-cache-ocqkz7.e1f1d6gn4 {
        position: fixed;
        bottom: 0px;
        width: 95%;
        z-index: 1000;
        border-radius: 5px;
        color: rgb(255 130 130);
        background-color: rgba(255, 255, 255, 0.9);
    }

    .st-emotion-cache-j78z8c.e1se5lgy0 {
        position: fixed;
        bottom: 85px;
        width: 95%;
        z-index: 1000;
        border-radius: 5px;
        color: rgb(255 130 130);
    
    }

    .element-container.st-emotion-cache-1oxz9gq.e1f1d6gn3 {
        display:none;
    }

    .st-emotion-cache-rp85x6.e1f1d6gn1 {
        display:none ;
    }

    .st-emotion-cache-1erivf3.e1b2p2ww15 {
        padding: 0rem;
        width: 10%;
    } 
    .st-emotion-cache-1gulkj5 {
        background-color: #f2f2f000;
    } 

    .st-emotion-cache-u8hs99.e1b2p2ww14 {
        display:none;
    } 

"""
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)


try:
    st.markdown("<p style='text-align: center; color: rgb(255, 75, 75); font-size: 90px;'>Ōrai</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>Hi {st.session_state['profile']['name']}!</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>How can I help you today?</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>You can ask me questions about Santander public and internal data. I will answer you the best I can,  \
                providing you document references and followups questions for each question you have.</p>", unsafe_allow_html=True)

    config = ConfigHelper.get_active_config_or_default()
    answering_prompt = config.prompts.answering_prompt
    default_questions = config.default_questions
    model = config.llm.model
    temperature = config.llm.temperature
    max_tokens = config.llm.max_tokens
    max_followups_questions = config.llm.max_followups_questions
    config_LLM = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_followups_questions": max_followups_questions
    }
    
    # with st.expander("Current configuration:"):
    #     st.button(f"**LLM model:** {model}")
    #     st.button(f"**LLM temperature:** {temperature}")
    #     st.button(f"**LLM max_tokens:** {max_tokens}")
    #     st.button(f"**LLM max_followups_questions:** {max_followups_questions}")
        
    st.markdown("Here are some examples of questions you can ask:")
    i = 0
    for default_question in default_questions:
        st.button(default_question, key=f"default_question_{i}", on_click=ask_followup_question, args=(default_question,))
        i += 1

    st.markdown("---------------------------------------")

    user_id = st.session_state["profile"]["user_id"]
    user_index_name = f"{user_id}-index" 
  
    init_chat_history()    
    st.session_state['conversation_id'] = str(uuid.uuid4())

    with st.sidebar:
        save_chat = st.button(":floppy_disk: Save conversation", key="save_chat")
        if save_chat:
            clear_chat_data(True, language)
        clear_chat = st.button(":speech_balloon: New conversation", key="clear_chat")
        if clear_chat:
            clear_chat_data(False, language)
        conversation_in_sidebar()
        
    ai_avatar_style = os.getenv("CHAT_AI_AVATAR_STYLE", "initials")
    ai_seed = os.getenv("CHAT_AI_SEED", "%C5%8C")
    user_avatar_style = os.getenv("CHAT_USER_AVATAR_STYLE", "initials")
    user_seed = os.getenv("CHAT_USER_SEED", st.session_state["profile"]["name"])

    uploaded_file_key = "uploaded_file_key"
    button_clicked_key = "button_clicked"

    container = st.container()
    with container:
        col1, col2 = st.columns([3, 1])
        with col1:
            input_text = st.text_input(" ", placeholder="Message Ōrai...", key="input"+str(st.session_state['input_message_key']), on_change=question_asked)
            st.markdown("I can make mistakes. Consider checking important information on document references | Beta v1.2 ")

        with col2:
            file_type = [processor.document_type for processor in config.document_processors]
            uploaded_files = st.file_uploader(
                                              label="Attach file:",
                                              type=file_type,
                                              accept_multiple_files=True,
                                              key=st.session_state["file_uploader_key"])
            if uploaded_files:
                files_names = []
                st.session_state["uploaded_files"] = uploaded_files                    
                backend_url = urllib.parse.urljoin(os.getenv('BACKEND_URL','http://localhost:7071'), "/api/BlobFileUpload")
                for up in uploaded_files:
                    bytes_data = up.getvalue()
                    print("BYTESSSSSS")
                    print(bytes_data)
                    print("FINNNNNNNNNNNNNNNNNNNNNN BYTES")
                    if st.session_state.get('filename', '') != up.name:
                        userid_filename = user_id + '/' + up.name
                        files_names.append(userid_filename)
                        print("up.name")
                        print(up.name)
                        
                        try:
                            response = requests.post(
                                    backend_url, 
                                    files={'file': bytes_data}, 
                                    data={"user_id": user_id, "file_name": up.name, "is_global_index": False}
                                )
                        except Exception as e:
                            st.error(traceback.format_exc())

                if len(uploaded_files) > 0:
                    # process_button = st.button("Click to start processing",
                    #                            on_click=remote_convert_files_and_add_embeddings,
                    #                            args=(files_names, user_index_name, False,))
                    # if process_button:     
                    #     st.session_state["file_uploader_key"] += 1
                    #     st.experimental_rerun()

                    # Testing Embeddings generation
                    process_button2 = st.button("Embeddings generation",
                                                key="Embeddings",
                                                on_click=embeddings_generation,
                                                args=(files_names, user_id, False,))
                    if process_button2:     
                        st.session_state["file_uploader_key"] += 1
                        st.experimental_rerun()

    conversation_id = st.session_state['conversation_id']
    question = st.session_state['chat_question']
    answer = ""
    citations = []

    container2 = st.container()
    with container2:
        if st.session_state.chat_askedquestion:
            st.session_state['chat_question'] = st.session_state.chat_askedquestion
            st.session_state.chat_askedquestion = ""
            user_message = st.session_state['chat_question']
            
            with st.spinner(text="Thinking...", cache=False):
                st.session_state['chat_history_langchain']["conversation_id"] = st.session_state['conversation_id']
                st.session_state['chat_history_langchain']["messages"].append({ "role": "user", "content": user_message })
                result = handle_message(st.session_state['chat_history_langchain'], language,user_index_name)
                st.session_state['chat_history_langchain']["messages"].append(result['choices'][0]['messages'][0])
                st.session_state['chat_history_langchain']["messages"].append(result['choices'][0]['messages'][1])
            
            content = json.loads(result['choices'][0]['messages'][0]['content'])
            sources = '  \n '.join([source["url"] for source in content['citations']])
            st.session_state['chat_source_documents'].append(sources)

            followupquestions = result['choices'][0]['messages'][1]['content']
            answer_without_followup, chat_followup_questions_list = extract_followupquestions(followupquestions)
            st.session_state['chat_followup_questions'] = chat_followup_questions_list

            previews = [source for source in content['citations']]
            st.session_state['chat_source_document_preview'].append(previews)
            
            answer_with_hyperlinks = add_hyperlinks(answer_without_followup, previews)
            st.session_state['chat_history'].append([st.session_state['chat_question'], answer_with_hyperlinks])

        if st.session_state['chat_history']:
            history_range = range(len(st.session_state['chat_history']))
            print("HISTORY_RANGE")
            print(history_range)
            print("CHAT HISTORY 11111111111111111")
            print(st.session_state['chat_history'])
            for i in history_range:
                print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                print(i)
                answer_with_citations = st.session_state['chat_history'][i][1]
                print("CHAT HISTORY 222222222222222222222222")
                print(st.session_state['chat_history'][i])
                print("CHAT HISTORY 333333333333333333333333333")
                print(st.session_state['chat_history'][i][:1])
                st.session_state['chat_history'][i] = st.session_state['chat_history'][i][:1] + [answer_with_citations]  

                answer = answer_with_citations

                print("CHAT HISTORY 4444444444444444444444444444444444")
                print(st.session_state['chat_history'][i])
                print("CHAT HISTORY 5555555555555555555555555555555555")
                print(st.session_state['chat_history'][i][0])
                message(st.session_state['chat_history'][i][0], is_user=True, key=str(i) + 'user' + '_user', avatar_style=user_avatar_style, seed=user_seed)
                message(answer_with_citations, key=str(i) + 'answers', avatar_style=ai_avatar_style, seed=ai_seed)
                print("CHAT HISOTORY")
                print(st.session_state['chat_history'])
                print("CHAT HISTORY[i][0]")
                print(st.session_state['chat_history'][i][0])
                citations = []
                st.markdown("<p style='text-align: right;'>Is this conversation helpful so far?</p>", unsafe_allow_html=True)
                feedback_key = f"feedback_{i}"
                feedback = streamlit_feedback(feedback_type="thumbs", optional_text_label="Please provide an explanation", key=feedback_key)
                if st.session_state['chat_source_document_preview'][i]:
                    with st.expander("**Here are the referenced documents:**"):
                        st.markdown("This section contains information related to the documents retrieved from my kwowledge base. Here you can access:\n - References or details about the documents, which could include links to the original documents.\n - Metadata, publication dates or any other relevant information associated with the retrieved search results.\n")
                        for j, source in enumerate(st.session_state['chat_source_document_preview'][i]):
                            button_opened = st.button(f'{j}. :bookmark_tabs: Page {source["page_number"] + 1} - {source["url"]}')
                            citations.append(source["url"])
                            st.session_state["conversation_sources_url"].append(source["url"])
                            if button_opened:
                                with st.sidebar:
                                    st.markdown('**Citations**')
                                    st.markdown(f'\n\n {source["content"]}', unsafe_allow_html=True)
                if feedback:
                    generate_json_feedback(feedback, question, answer, citations, conversation_id, config_LLM, answering_prompt)

                if i == len(st.session_state['chat_history']) - 1:
                    if len(st.session_state['chat_followup_questions']) > 0:
                        st.markdown('**I suggest these related questions for you:**')
                        with st.container():
                            for questionId, followup_question in enumerate(st.session_state['chat_followup_questions']):
                                if followup_question:
                                    str_followup_question = re.sub(r"(^|[^\\\\])'", r"\1\\'", followup_question)
                                    st.button(str_followup_question, key=randint(1000, 99999), on_click=ask_followup_question, args=(followup_question, ))
except Exception:
    st.error(traceback.format_exc())