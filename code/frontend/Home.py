import os
import json
import yaml
import logging
import requests
import streamlit as st
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from yaml.loader import SafeLoader
from streamlit_extras.switch_page_button import switch_page
from msal_streamlit_authentication import msal_authentication

load_dotenv()

logger = logging.getLogger(
    'azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Home", page_icon=os.path.join(
    'images', 'favicon.ico'), layout="wide", menu_items=None, initial_sidebar_state="collapsed")

mod_page_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(mod_page_style, unsafe_allow_html=True)

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)


def clear_session():
    for key in st.session_state.keys():
        del st.session_state[key]


with open('config/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

st.markdown("<p style='text-align: center; color: rgb(255, 75, 75); font-size: 90px;'>Ōrai</p>",
            unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Get started!</h2>",
            unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )
    name, authentication_status, username = authenticator.login('Login', 'main')
    if st.session_state["authentication_status"]:
        profile = {}
        if name:
            for user in config["users"]: 
                if name == config["users"][user]["name"]:
                    profile["email"] = config["users"][user]["email"]
                    profile["group"] = config["users"][user]["group"]
                    profile["name"] = config["users"][user]["name"]
                    profile["user_id"] = config["users"][user]["user_id"]
            if profile:
                st.session_state["profile"] = profile
                switch_page("Chat")

    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')

    st.markdown("---------------------------------------")

    custom_css = """
        .st-emotion-cache-1wmy9hl.e1f1d6gn0 {
            max-width: auto;
            margin-left: auto;
            margin-right: auto;
        } 
        .st-emotion-cache-18ni7ap.ezrtsby2 {
            visibility: hidden;
        
        }

    """
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)    

with st.container():
    st.markdown("<h3 style='text-align: center;'>Single Sign-On</h3>",unsafe_allow_html=True) 
    orai_groups = {
        "groups" : {
            os.getenv("ORAI_ADMIN_USER_GROUP_ID"): os.getenv("ORAI_ADMIN_USER_GROUP_NAME"),
            os.getenv("ORAI_ADVANCE_USER_GROUP_ID"): os.getenv("ORAI_ADVANCE_USER_GROUP_NAME"),
            os.getenv("ORAI_METRICS_GROUP_ID"): os.getenv("ORAI_METRICS_GROUP_NAME"),
            os.getenv("ORAI_USER_GROUP_ID"): os.getenv("ORAI_USER_GROUP_NAME"),
        }
    }
    login_token = msal_authentication(
        auth={
            "clientId": os.getenv("CLIENT_ID"),
            "authority": os.getenv("AUTHORITY"),
            "redirectUri": os.getenv("REDIRECT_URI"),
            "postLogoutRedirectUri": "/"
        },
        cache={
            "cacheLocation": "sessionStorage",
            "storeAuthStateInCookie": False
        },
        login_request={
            "scopes": ["openid"]
        },
        logout_request={},
        login_button_text="Continue with Santander account",
        class_name="css_button_class_selector",
        html_id="html_id_for_button",
        key=1
    )

    def get_user_groups(token: str, user_id: str) -> list:
        graph_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/getMemberGroups'

        headers = { 'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json', }
    
        data = { 'securityEnabledOnly': True }

        response = requests.post(graph_url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            groups = response.json()
            return groups['value']
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
        return []

    if login_token:
        user_groups = get_user_groups(login_token["accessToken"],
                                    login_token["account"]["localAccountId"])
        groups = []
        for group_id in user_groups:
            for k, v in orai_groups["groups"].items():
                if k == group_id:
                    groups.append(v)

        profile = {
            "user_id": login_token["account"]["localAccountId"],
            "name": login_token["account"]["name"],
            "email": login_token["account"]["username"],
            "group": groups[0],
        }
        
        if profile:
            st.session_state["profile"] = profile
            switch_page("Chat")

st.markdown("---------------------------------------")

footer_text = """
<div style="text-align: center; margin-top: 30px">
    <p>Terms of Use | Privacy Policy | Contact Us</p>
    <p>©Santander 2024. All rights reserved.</p>
</div>
"""
st.markdown(footer_text, unsafe_allow_html=True)