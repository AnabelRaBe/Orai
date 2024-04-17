import os
import logging
import traceback
import streamlit as st
from streamlit_tags import st_tags
from dotenv import load_dotenv
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
import time
import sys
sys.path.append("..")
from utilities.helpers.ConfigHelper import ConfigHelper

load_dotenv()

logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
st.set_page_config(page_title="Configuration", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)

mod_page_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(mod_page_style, unsafe_allow_html=True)

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

st.title('Configure Prompts and Logging')
st.markdown("Configure the prompts that are used to answer the user's question, and the logging settings. Dont forget to save your configuration!")
st.markdown("---------------------------------------")

config = ConfigHelper.get_active_config_or_default()

def init_configuration():
    if 'answering_prompt' not in st.session_state:
        st.session_state['answering_prompt'] = config.prompts.answering_prompt
    if 'post_answering_prompt' not in st.session_state:
        st.session_state['post_answering_prompt'] = config.prompts.post_answering_prompt
    if 'enable_post_answering_prompt' not in st.session_state:
        st.session_state['enable_post_answering_prompt'] = config.prompts.enable_post_answering_prompt
    if 'post_answering_filter_message' not in st.session_state:
        st.session_state['post_answering_filter_message'] = config.messages.post_answering_filter
    if 'faq_answering_prompt' not in st.session_state:
        st.session_state['faq_answering_prompt'] = config.prompts.faq_answering_prompt
    if 'faq_content' not in st.session_state:
        st.session_state['faq_content'] = config.prompts.faq_content

    if 'default_questions' not in st.session_state:
        st.session_state['default_questions'] = config.default_questions

    # st.session_state['log_user_interactions'] = config.logging.log_user_interactions
    if 'log_tokens' not in st.session_state:
        st.session_state['log_tokens'] = config.logging.log_tokens
    if 'orchestrator_strategy' not in st.session_state:
        st.session_state['orchestrator_strategy'] = config.orchestrator.strategy.value

    if 'llm_model' not in st.session_state:
        st.session_state['llm_model'] = config.llm.model
    if 'llm_max_tokens' not in st.session_state:
        st.session_state['llm_max_tokens'] = config.llm.max_tokens
    if 'llm_temperature' not in st.session_state:
        st.session_state['llm_temperature'] = config.llm.temperature
    if 'llm_top_p' not in st.session_state:
        st.session_state['llm_top_p'] = config.llm.top_p
    if 'max_followups_questions' not in st.session_state:
        st.session_state['max_followups_questions'] = config.llm.max_followups_questions
    if 'llm_embeddings_model' not in st.session_state:
        st.session_state['llm_embeddings_model'] = config.llm_embeddings.model

    if 'global_business_metadata' not in st.session_state:
        st.session_state['global_business_metadata'] = config.metadata.global_business
    if 'divisions_and_areas_metadata' not in st.session_state:
        st.session_state['divisions_and_areas_metadata'] = config.metadata.divisions_and_areas
    if 'tags_metadata' not in st.session_state:
        st.session_state['tags_metadata'] = config.metadata.tags
    if 'regions_and_countries_metadata' not in st.session_state:
        st.session_state['regions_and_countries_metadata'] = config.metadata.regions_and_countries
    if 'languages_metadata' not in st.session_state:
        st.session_state['languages_metadata'] = config.metadata.languages
    if 'years_metadata' not in st.session_state:
        st.session_state['years_metadata'] = config.metadata.years
    if 'periods_metadata' not in st.session_state:
        st.session_state['periods_metadata'] = config.metadata.periods
    if 'importances_metadata' not in st.session_state:
        st.session_state['importances_metadata'] = config.metadata.importances
    if 'securities_metadata' not in st.session_state:
        st.session_state['securities_metadata'] = config.metadata.securities
    if 'origins_metadata' not in st.session_state:
        st.session_state['origins_metadata'] = config.metadata.origins
    if 'domains_metadata' not in st.session_state:
        st.session_state['domains_metadata'] = config.metadata.domains

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

def show_metadata(metadata_list: list):
    num_columns = 4
    cols = st.columns(num_columns)
    i=0

    for elem in metadata_list:
        with cols[i]:
            st.markdown(f"""- {elem}""")
        i = i+1
        if i == num_columns:
            i = 0

def modified_metadata(metadata_name: str, global_variable: str):
    st.markdown(f"""
    ### {metadata_name}
    """)

    metadata_list = st.session_state[f'{global_variable}_metadata'] 

    show_metadata(metadata_list)
    
    with st.expander(f"Change the options of {metadata_name}", expanded=True):
        new_metadata = st_tags(
            label = f"Write the {metadata_name} you want to add...",
            text='Press enter to add more...',
            value=[],
            suggestions=[],
            maxtags = 100,
            key=f'tags-file-{global_variable}')
        
        for metadata in new_metadata:
            metadata = metadata.capitalize()
            if metadata not in metadata_list:
                metadata_list.append(metadata)

        st.session_state[f'{global_variable}_metadata'] = metadata_list

        metadata_delete = st.multiselect(label=f"Delete {metadata_name}", key=f"delete-{global_variable}", placeholder=f"Select the {metadata_name} you want delete...", options=metadata_list)

        if st.button(label=f"Delete {metadata_name}", key=f"delete-{global_variable}-button"):
            for option_delete in metadata_delete:
                if option_delete in metadata_list:
                    metadata_list.remove(option_delete)
            st.session_state[f'{global_variable}_metadata'] = metadata_list
            switch_page("Configuration")

def modified_regions_countries():
    st.markdown(f"""
    ### Regions and countries
    """)

    regions = st.session_state['regions_and_countries_metadata'].keys()

    show_metadata(regions)

    with st.expander(f"Change the options of regions", expanded=True):
            new_metadata = st_tags(
                label = f"Write the regions you want to add...",
                text='Press enter to add more...',
                value=[],
                suggestions=[],
                maxtags = 100,
                key=f'tags-file-regions')
            
            for new_region in new_metadata:
                new_region = new_region.capitalize()
                if new_region not in st.session_state['regions_and_countries_metadata']:
                    st.session_state['regions_and_countries_metadata'][new_region] = []

            metadata_delete = st.multiselect(label=f"Delete regions", key=f"delete-region", placeholder=f"Select the regions you want delete...", options=regions)

            if st.button(label=f"Delete regions", key=f"delete-regions-button"):
                for option_delete in metadata_delete:
                    if option_delete in regions:
                        del st.session_state['regions_and_countries_metadata'][option_delete]
                switch_page("Configuration")
            

    for region, countries in st.session_state['regions_and_countries_metadata'].items():
        st.markdown(f"""
        #### {region}
        """)
        show_metadata(countries)

        with st.expander(f"Change the options of countries in {region}", expanded=True):
            new_metadata = st_tags(
                label = f"Write the countries from {region} you want to add...",
                text='Press enter to add more...',
                value=[],
                suggestions=[],
                maxtags = 100,
                key=f'tags-file-{region}')
                        
            for metadata in new_metadata:
                metadata = metadata.capitalize()
                if metadata not in countries:
                    countries.append(metadata)

            st.session_state['regions_and_countries_metadata'][region] = countries

            metadata_delete = st.multiselect(label=f"Delete countries from {region}", key=f"delete-{region}", placeholder=f"Select the countries from {region} you want delete...", options=countries)

            if st.button(label=f"Delete countries", key=f"delete-{region}-button"):
                for option_delete in metadata_delete:
                    if option_delete in countries:
                        countries.remove(option_delete)
                st.session_state['regions_and_countries_metadata'][region] = countries
                switch_page("Configuration")


try:
    init_configuration()
    
    st.markdown("""
    ## Orchestrator strategy
    The orchestrator strategy determines how the knowledge base is used to answer the user's question. The following strategies are available:
    - `langchain`: The langchain strategy uses the knowledge base to answer the user's question. Langchain is a python library that allows to chain multiple language models together. The knowledge base is used to retrieve the sources, and the sources are used to answer the user's question.
    """)
    with st.expander("Orchestrator configuration", expanded=True):
        cols = st.columns([2,4])
        with cols[0]:
            st.selectbox("Orchestrator strategy", key='orchestrator_strategy' , options=config.get_available_orchestration_strategies())
    
    st.markdown("""
    ## LLM's configuration
    The LLM's configuration allows you to configure the LLM's that are used to answer the user's question. The following options are available:
    - `model`: The LLM model that is used to answer the user's question. The following models are available right now:
        - `gpt-4`
        - `gpt-4-turbo`
    - `max_tokens`: The maximum number of tokens that are generated by the LLM.
    - `temperature`: The temperature that is used to generate the tokens.
    - `top_p`: The top p value that is used to generate the tokens.
    """)
    with st.expander("LLM models selection and configuration", expanded=True):
        st.selectbox("LLM model", key='llm_model', options=config.get_available_llm_models())
        st.number_input("LLM max tokens", key='llm_max_tokens', min_value=500, max_value=3000, value=3000)
        st.number_input("LLM temperature", key='llm_temperature', min_value=0.0, max_value=2.0, value=0.7)
        st.number_input("LLM top p", key='llm_top_p', min_value=0.0, max_value=1.0, value=1.0)
        st.number_input("Max numbers of follow-ups questions", key='max_followups_questions', min_value=3, max_value=5, value=3)
    
    with st.expander("LLM embeddings models", expanded=True):
        st.selectbox("LLM embeddings model", key='llm_embeddings_model', options=config.get_available_llm_embeddings_models())
    
    answering_prompt_help = "This prompt is used to answer the user's question, using the sources that were retrieved from the knowledge base."
    post_answering_prompt_help = "You can configure a post prompt that allows to fact-check or process the answer, given the sources, question and answer. This prompt needs to return `True` or `False`."
    post_answering_filter_help = "The message that is returned to the user, when the post-answering prompt returns."
    question_help = "This is where you enter the questions shown in the examples on the chat page."
    faq_answering_prompt_help = "This prompt is used to answer the user's question about Chatbot identity and assistance."
    faq_content_help = "This is where you enter the FAQ content."

    st.markdown("""
    ## Default Questions
    Here you can change the suggested questions that appear in the chat.
    """)
    
    for question in st.session_state['default_questions']:
        st.markdown(f"- {question}") 

    with st.expander("Default questions", expanded=True):
        default_questions_paragraph = st.text_input(label="Write yours questions and separate by semicolon (;). Example: ¿Qué es Banco Santander?;¿Puedes resumir los puntos más importantes de la guía de uso de Orai?;¿Cuál es el objetivo financiero de Banco Santander para 2025?",
                                                    key="default_questions_text_input")
        if default_questions_paragraph != "":
            default_questions_list = default_questions_paragraph.split(";")
            st.session_state['default_questions'] = default_questions_list
            
    st.markdown("""
    ## Prompts Configuration""")
    st.markdown("""
    ### Question and Answering Tool configuration
    #### Question Answering prompt template
    The answering prompt template is used to answer the user's question, using the sources that were retrieved from the knowledge base. The following variables can be used in the answering prompt:
    - `{sources}`: The sources that were retrieved from the knowledge base.
    - `{question}`: The user's question.
    - `{current_date}`: The current date in the format `dd/mm/yyyy` to be used in the answering prompt in order to resolve temporal concepts.
    - `{max_followups_questions}`: The maximum number of follow-up questions that can be asked.
    """)
    with st.expander("Question and Answering Tool configuration", expanded=True):
        st.text_area("Answering prompt", key='answering_prompt', on_change=validate_answering_prompt, help=answering_prompt_help, height=400)

    st.markdown("""
    ### FAQ Tool configuration
    #### FAQ prompt template
    The answering prompt template is used to answer the user's question, using the sources that were retrieved from the knowledge base. The following variables can be used in the answering prompt:
    - `{content}`: The sources that were retrieved from the knowledge base.
    - `{question}`: The user's question.
    - `{max_followups_questions}`: The maximum number of follow-up questions that can be asked.
    """)
    with st.expander("FAQ Tool configuration", expanded=True):
        st.text_area("FAQ answering prompt", key='faq_answering_prompt', help=faq_answering_prompt_help, height=200)
        st.text_area("FAQ content", key='faq_content', help=faq_content_help, height=200)
    
    st.markdown("""
    ### Post-answering configuration
    #### Post-answering prompt template
    You can configure a post prompt that allows to fact-check or process the answer, given the sources, question and answer. This prompt needs to return `True` or `False`. The following variables can be used in the post-answering prompt:
    - `{sources}`: The sources that were retrieved from the knowledge base.
    - `{question}`: The user's question.
    - `{answer}`: The answer that was generated using the answering prompt.   
    #### Post-answering filter message template
    The message that is returned to the user, when the post-answering prompt returns `False`.
    """)
    with st.expander("Prompt configuration", expanded=True):
        st.text_area("Post-answering prompt", key='post_answering_prompt', on_change=validate_post_answering_prompt, help=post_answering_prompt_help, height=200)
        st.checkbox('Enable post-answering prompt', key='enable_post_answering_prompt')
        st.text_area("Post-answering filter message", key='post_answering_filter_message', help=post_answering_filter_help, height=200)        

    document_processors = list(map(lambda x: {
        "document_type": x.document_type, 
        "chunking_strategy": x.chunking.chunking_strategy.value, 
        "chunking_size": x.chunking.chunk_size,
        "chunking_overlap": x.chunking.chunk_overlap, 
        "loading_strategy": x.loading.loading_strategy.value,
        }, config.document_processors))

    st.markdown("""   
    ## Document processing configuration
    The document processing configuration allows you to configure how the documents are processed. The following options are available:
    - `document_type`: The type of document that is processed. The following document types are available:
        - `text`: The document is a text document.
        - `pdf`: The document is a PDF document.
        - `docx`: The document is a Word document.
    - `chunking_strategy`: The chunking strategy that is used to split the document into chunks. The following chunking strategies are available:
        - `no_chunking`: The document is not split into chunks.
        - `fixed_size`: The document is split into chunks of a fixed size.
        - `fixed_number`: The document is split into a fixed number of chunks.
    - `chunking_size`: The size of the chunks, when the chunking strategy is `fixed_size`.
    - `chunking_overlap`: The overlap between the chunks, when the chunking strategy is `fixed_size`.
    - `loading_strategy`: The loading strategy that is used to load the document. The following loading strategies are available:
        - `full_document`: The full document is loaded into memory.
        - `chunked`: The document is loaded in chunks.
    """)
    with st.expander("Document processing configuration", expanded=True):
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
    
    st.markdown("""
    ## Logging configuration
    The logging configuration allows you to configure what is logged. The following options are available:
    - `log_user_interactions`: Log user input and output (questions, answers, chat history, sources).
    - `log_tokens`: Log tokens.
    """)
    with st.expander("Logging configuration", expanded=True):       
        st.checkbox('Log tokens', key='log_tokens')
    
    st.markdown("""
    ## Metadata
    In this section you can add or delete options in each metadata files:
    - `global_business`: this variable has the different options of global business.
    - `divisions_and_areas`: this variable has the different options of divisions and areas.
    - `tags`: this variable has the different options of tags.
    - `regions_and_countries`: this variable has the different options of regions and the countries that each region has.
    - `languages`: this variable has the different options of languages.
    - `year`: this variable has the different options of year.
    - `period`: this variable has the different options of period.
    - `importance`: this variable has the different options of importnace.
    - `security`: this variable has the different options of security.
    - `origin`: this variable has the different options of origin.
    - `domain`: this variable has the different options of domain.
    """)

    modified_metadata("Global business", "global_business")
    modified_metadata("Divisions and areas", "divisions_and_areas")
    modified_metadata("Tags", "tags")
    modified_regions_countries()
    modified_metadata("Languages", "languages")
    modified_metadata("Years", "years")
    modified_metadata("Periods", "periods")
    modified_metadata("Importances", "importances")
    modified_metadata("Securities", "securities")
    modified_metadata("Origins", "origins")
    modified_metadata("Domains", "domains")
    
    st.markdown("---------------------------------------")

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
        current_config = {
            "welcome_message": config.welcome_message,
            "default_questions": st.session_state['default_questions'],
            "prompts": {
                "condense_question_prompt": "",
                "answering_prompt": st.session_state['answering_prompt'],
                "post_answering_prompt": st.session_state['post_answering_prompt'],
                "enable_post_answering_prompt": st.session_state['enable_post_answering_prompt'],
                "faq_answering_prompt": st.session_state['faq_answering_prompt'],
                "faq_content": st.session_state['faq_content'],
            },
            "messages": {
                "post_answering_filter": st.session_state['post_answering_filter_message']
            },
            "document_processors":  document_processors,
            "logging": {
                "log_tokens": st.session_state['log_tokens']
            },
            "orchestrator": {
                "strategy": st.session_state['orchestrator_strategy']
            },
            "llm": {
                "model": st.session_state['llm_model'],
                "max_tokens": st.session_state['llm_max_tokens'],
                "temperature": st.session_state['llm_temperature'],
                "top_p": st.session_state['llm_top_p'],
                "max_followups_questions": st.session_state['max_followups_questions']
            },
            "llm_embeddings": {
                "model": st.session_state['llm_embeddings_model']
            },
            "metadata": {
                "global_business": st.session_state['global_business_metadata'],
                "divisions_and_areas": st.session_state['divisions_and_areas_metadata'],
                "tags": st.session_state['tags_metadata'],
                "regions_and_countries": st.session_state['regions_and_countries_metadata'],
                "languages": st.session_state['languages_metadata'],
                "years": st.session_state['years_metadata'],
                "periods": st.session_state['periods_metadata'],
                "importances": st.session_state['importances_metadata'],
                "securities": st.session_state['securities_metadata'],
                "origins": st.session_state['origins_metadata'],
                "domains": st.session_state['domains_metadata']
            }
        }
        ConfigHelper.save_config_as_active(current_config)
        st.success("Configuration saved successfully!")

except Exception as e:
    st.error(traceback.format_exc())