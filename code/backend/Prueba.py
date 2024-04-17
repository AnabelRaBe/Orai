import os
import json
import logging
import requests
from dotenv import load_dotenv
# from ..utilities.helpers.OrchestratorHelper import Orchestrator
# from ..utilities.helpers.ConfigHelper import ConfigHelper
# from ..utilities.helpers.HyperlinksHelper import Hyperlinks
from utilities.helpers.OrchestratorHelper import Orchestrator
from utilities.helpers.ConfigHelper import ConfigHelper
from utilities.helpers.HyperlinksHelper import Hyperlinks
import sys



print("VERSIÓN DE PYTHON")
print(sys.version)
logging.info('Requested to start processing the conversation using langchain orchestrator')

load_dotenv()

config = ConfigHelper.get_active_config_or_default()

data = {
    "chat_history": {
        "messages": [
            {
                "role": "user",
                "content": "¿Cuál fue la nota de prensa de santander en 2023?"
            }
        ],
        "conversation_id": "243a6c7c-c53d-40ad-b354-1f5d290a7a47"
    },
    "language": "Spanish",
    "user_index_name": "9e74a326-1a4a-4f41-9b62-7c1793e85f48-index"
}

request = data['chat_history']

#############################################
# 1. Append el campo messages de chat_history en BBDD
# 2. Sustituyo request["messages"] por messages en BBDD
#############################################

language = data['language']
user_index_name = data['user_index_name']

message_orchestrator = Orchestrator()
hyperlinks = Hyperlinks()

try:
    user_message = request["messages"][-1]['content']
    conversation_id = request["conversation_id"]
    user_assistent_messages = list(filter(lambda x: x['role'] in ('user', 'assistant'), request["messages"][0:-1]))  

    chat_history = []
    for i, k in enumerate(user_assistent_messages):
        if i % 2 == 0:
            chat_history.append((user_assistent_messages[i]['content'], user_assistent_messages[i+1]['content']))

    messages = message_orchestrator.handle_message(user_message=user_message, language = language,chat_history=chat_history,
                                                    conversation_id=conversation_id, orchestrator=config.orchestrator,
                                                    global_index_name=os.getenv("AZURE_SEARCH_INDEX"), user_index_name=user_index_name, config=config)

    chat_followup_questions_list = []

    for message in messages:
        if message["role"] == "assistant":
            answer_without_followup, chat_followup_questions_list = message_orchestrator.extract_followupquestions(message["content"])
            message["content"] = answer_without_followup

    response = {
        "id": "response.id",
        "model": os.getenv("AZURE_OPENAI_MODEL"),
        "created": "response.created",
        "object": "response.object",
        "choices": [
            {
                "messages": messages,
                "followupquestions": chat_followup_questions_list
            }
        ]
    }

    answer_with_hyperlinks = hyperlinks.add_hyperlinks(response, answer_without_followup)

    for message in messages:
        if message["role"] == "assistant":
            message["content"] = answer_with_hyperlinks

    response = {
        "id": "response.id",
        "model": os.getenv("AZURE_OPENAI_MODEL"),
        "created": "response.created",
        "object": "response.object",
        "choices": [
            {
                "messages": messages,
                "followupquestions": chat_followup_questions_list
            }
        ]
    }

    print("FINNNNNNNNNNNNNNNNNNNN")
    print(messages)

    #############################################
    # 3. Append el campo messages de response en BBDD
    #############################################
    # ¿En qué momento solicitan el histórico para pintarlo? 
        # Primero piden el histórico GetChatHistory endpoint. 
        # Le damos lo que tenemos hasta el momento de la conversacion_Id
        # Luego hacen la llamada al orquestador para su nueva pregunta
    # ¿Qué le tenemos que devolver? 
        #¿Basta con el campo message que hemos estado almacenando en BBDD?
        #Las referencias se introdujeron en la respuesta, por tanto ya se están insertando en la BBDD
        # Las preguntas sugeridas sólo se muestra de la última respuesta, por tanto, no hace falta
    # Puede que los append que haga langchain.postgres no introduzcan en la BBDD 
    # la estructura que nos interesa para langchain_chat_history o chat_history
    # ¿Quizás tengamos que usar update u otro tipo de sentencias?
    #############################################
    print("Exception in langchain orchestrator")
    #print(json.dumps(response), status_code=200, mimetype="application/json") 
except Exception as e:
    print("Exception in langchain orchestrator")
    #print(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 


