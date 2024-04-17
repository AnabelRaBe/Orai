import os
import io
import traceback
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from utilities.helpers.ConfigHelper import ConfigHelper
import sys
sys.path.append("..")
from utilities.helpers.AzureSearchHelper import AzureSearchHelper
from utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient

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

if st.session_state["profile"]["group"] != "Orai_Admin" and st.session_state["profile"]["group"] != "Orai_Metrics":
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


def plot_metric(thumbs_up: int, thumbs_down: int):
    chart_data = pd.DataFrame({'Labels': ['Positive', 'Negative'], 'Values': [thumbs_up, thumbs_down]})

    fig = px.pie(chart_data, names='Labels', values='Values', 
                color_discrete_sequence=['#2ecc71','#e74c3c'],
                color= "Labels",
                title=f'Positive vs. Negative. \
                      Total feedbacks: {thumbs_up + thumbs_down}')
    
    fig.update_traces(textinfo='percent+label', pull=[0.1, 0], hole=0.3)

    st.plotly_chart(fig)

def compute_global_metrics(feedback: dict, thumbs_up: int, thumbs_down: int):
    positive = "\U0001f44d"
    negative = "\U0001f44e"

    score = feedback.get("score", "")
    if score == positive:
        thumbs_up += 1
    elif score == negative:
        thumbs_down += 1

    return thumbs_up,thumbs_down

def compute_user_metrics(feedbacks: list, thumbs_up: int, thumbs_down: int):
    positive = "\U0001f44d"
    negative = "\U0001f44e"

    for feedback in feedbacks:
        score = feedback.get("score", "")
        if score == positive:
            thumbs_up += 1
        elif score == negative:
            thumbs_down += 1

    return thumbs_up,thumbs_down
    
def show_percentage_users(message: str):
    if percentage_feedback < 5:
        st.error(message)
    elif percentage_feedback < 25:
        st.warning(message) 
    else:
        st.success(message)

def generate_file_name(name: str, extension: str) -> str:
    now = datetime.now()
    file_name = f"{name}_feedback_{now.strftime('%Y-%m-%d_%H-%M-%S')}.{extension}"
    return file_name

def prepare_conversation_txt(feedbacks: list, thumbs_up: int, thumbs_down: int) -> str:
    conversation = ""
    conversation += f"\n**************************************************\n"
    conversation += "Positive feedback can appear as 'U0001f44d' or 👍 \nNegative feedback can appear as 'U0001f44e' or 👎"
    conversation += f"\n**************************************************\n"

    conversation += "\n--------------------------------------------------------------------------------------------------------------------------------------------------------\nMetrics\n--------------------------------------------------------------------------------------------------------------------------------------------------------\n\n"
    conversation += f"Total feedbacks = {thumbs_up + thumbs_down}\n"
    conversation += f"Positive feedbacks 👍 = {thumbs_up}\n"
    conversation += f"Negative feedbacks 👎 = {thumbs_down}\n\n"

    conversation += "\n--------------------------------------------------------------------------------------------------------------------------------------------------------\nFeedbacks\n--------------------------------------------------------------------------------------------------------------------------------------------------------\n"
    for feedback in feedbacks:
        conversation += f"\n........................................................................................................................................................\n{feedback['user_id']}'s feedback\n........................................................................................................................................................\n\n"
        conversation += f"Feedback: {feedback['feedback']['score']}\n"
        if feedback['feedback']['text']:
            conversation += f"Comment: {feedback['feedback']['text']}\n\n"
        else:
            conversation +="\n"
        conversation += f"Date: {feedback['date']}\n\n"
        conversation += f"Question: {feedback['question']}\n\n"
        conversation += f"Answer: {feedback['answer']}\n\n\n"
        conversation += f"Json:\n{feedback}\n\n"

    return conversation

def prepare_conversation_xlsx(feedbacks: list) -> str:
    feedback_df = pd.DataFrame(columns=["User ID", "Name", "Date", "Comment", "Question", "Answer", "Prompt","Score", "Fix", "Model Name", "Model Temperature", "Model Max Tokens"])
    for feedback in feedbacks:
        if feedback["feedback"]["score"] == "👎":
            date = datetime.strptime(feedback["date"], "%Y-%m-%d_%H-%M-%S").date()
            date = date.strftime("%Y/%m/%d")
            feedback_df = feedback_df.append({
                                "User ID": feedback["user_id"],
                                "Name": feedback["name"],
                                "Date": date,
                                "Comment": feedback["feedback"]["text"],
                                "Question": feedback["question"],
                                "Answer": feedback["answer"],
                                "Prompt": feedback["prompt"],
                                "Score": "Negative",
                                "Fix": "",
                                "Model Name": feedback["model_configuration"]["model"],
                                "Model Temperature": feedback["model_configuration"]["temperature"],
                                "Model Max Tokens": feedback["model_configuration"]["max_tokens"]
                            }, ignore_index=True)
    return feedback_df

def convert_to_xlsx(df, writer):
    return df.to_excel(writer, sheet_name='Sheet1', index=False)

try:
    st.title('Global Feedback Metrics')
    st.markdown("This section allows you to explore the global feedback.")
  
    azure_blob_client = AzureBlobStorageClient(account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME"), account_key = os.getenv("AZURE_BLOB_ACCOUNT_KEY"), container_name = os.getenv("AZURE_BLOB_CONTAINER_FEEDBACK_NAME"))
    feedbacks = azure_blob_client.get_all_files_feedback(container_name = os.getenv("AZURE_BLOB_CONTAINER_FEEDBACK_NAME"))
    
    global_thumbs_up = 0
    global_thumbs_down = 0

    users = {}
    users_feedback = {}

    for feedback in feedbacks:

        global_thumbs_up, global_thumbs_down = compute_global_metrics(feedback["feedback"], global_thumbs_up, global_thumbs_down)

        if feedback["user_id"] in users.keys():
            users[feedback["user_id"]].append(feedback["feedback"])
            users_feedback[feedback["user_id"]].append(feedback)
        else:
            users[feedback["user_id"]] = [feedback["feedback"]]
            users_feedback[feedback["user_id"]] = [feedback]
    
    total_users = 100
    num_users_feedback = len(users)
    percentage_feedback = (num_users_feedback / total_users) * 100

    global_message = ""
    if num_users_feedback == 1:
        global_message = f":bar_chart: Of the {total_users} total users, **{num_users_feedback}** user has provided feedback. That is, **{percentage_feedback:.2f}%** of the users."
    else:
        global_message = f":bar_chart: Of the {total_users} total users, **{num_users_feedback}** users have provided feedback. That is, **{percentage_feedback:.2f}%** of the users."

    show_percentage_users(global_message)
            
    with st.expander("Global Metrics", expanded=True):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            plot_metric(global_thumbs_up, global_thumbs_down)
        st.download_button(
            label=f":arrow_down_small: Download global feedback (.txt)",
            data=prepare_conversation_txt(feedbacks, global_thumbs_up, global_thumbs_down),
            key=f"button-download-global-feedback-txt",
            file_name=generate_file_name(name="global", extension="txt")
        )
        buffer = io.BytesIO()
        feedback_df = prepare_conversation_xlsx(feedbacks)
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            convert_to_xlsx(feedback_df, writer)
            writer.save()
            st.download_button(
                label=f":arrow_down_small: Download global feedback (.xlsx)",
                data=buffer,
                key=f"button-download-global-feedback-xlsx",
                file_name=generate_file_name(name="global", extension="xlsx"),
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    st.markdown("---------------------------------------")
    st.title('Local Feedback Metrics')
    st.markdown("This section allows you to explore the feedback by user id.")

    local_message = ""
    if num_users_feedback == 1:
        local_message = f":bar_chart: **{num_users_feedback}** user (**{percentage_feedback:.2f}%**) has provided feedback."
    else:
        local_message = f":bar_chart: **{num_users_feedback}** users (**{percentage_feedback:.2f}%**) have provided feedback."

    show_percentage_users(local_message)

    for user in users.keys():

        user_thumbs_up = 0
        user_thumbs_down = 0

        with st.expander(label= user, expanded=False):
            user_thumbs_up, user_thumbs_down = compute_user_metrics(users[user], user_thumbs_up, user_thumbs_down)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                plot_metric(user_thumbs_up, user_thumbs_down)
            st.download_button(
                label=f":arrow_down_small: Download {user} feedback (.txt)",
                data=prepare_conversation_txt(users_feedback[user], user_thumbs_up, user_thumbs_down),
                key=f"button-download-{user}-feedback-txt",
                file_name=generate_file_name(name=user, extension="txt")
            )

            buffer = io.BytesIO()
            feedback_df = prepare_conversation_xlsx(users_feedback[user])
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                convert_to_xlsx(feedback_df, writer)
                writer.save()
                st.download_button(
                    label=f":arrow_down_small: Download {user} feedback (.xlsx)",
                    data=buffer,
                    key=f"button-download-{user}-feedback-xlsx",
                    file_name=generate_file_name(name=user, extension="xlsx"),
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
except Exception as e:
    st.error(traceback.format_exc())