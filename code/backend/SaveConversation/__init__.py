import logging
import datetime
import json
import azure.functions as func
from ..utilities.common.GenerateTopicTool import GenerateTopicTool
from ..utilities.common.PostgreSQL import PostgreSQL
from ..utilities.common.ValidationRequest import RequestSave
from dotenv import load_dotenv


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Request saves conversation in a PostgreSQL database')

    load_dotenv()

    try:
        request_body = RequestSave(**req.get_json())

        now = datetime.datetime.now()
        timestamptz = now.isoformat()
        postgresql = PostgreSQL()

        rows = postgresql.select_data("conversations", f"conversation_id = '{request_body.conversation_id}' AND user_id = '{request_body.user_id}'", 'save_chat, language, topic')
        if not rows:
            user = postgresql.select_data("users", f"user_id = '{request_body.user_id}'")
            if not user:
                postgresql.insert_data("users", f"'{request_body.user_id}', '{request_body.user_name}', '{timestamptz}'", "(user_id, username, created_at)")
            postgresql.insert_data("conversations", f"'{request_body.conversation_id}', '{request_body.user_id}', '{request_body.save_chat}', '{request_body.language}', '{timestamptz}', '{timestamptz}'", "(conversation_id, user_id, save_chat, language, created_at, modified_at)")
        
        if request_body.message:
            for message in request_body.message:
                message = str(message).replace("'", '"')
                id_message = postgresql.get_max_id_by_conversation_id("messages", request_body.conversation_id) + 1
                postgresql.insert_data("messages", f"'{request_body.conversation_id}', {id_message}, '{message}', '{timestamptz}'", "(conversation_id, id_message, message_text, created_at)")
            postgresql.update_data("conversations", f"modified_at = '{timestamptz}'", f"conversation_id = '{request_body.conversation_id}' AND user_id = '{request_body.user_id}'")

        if (request_body.save_chat or len(rows) > 0 and rows[0][0]) and len(rows) > 0 and rows[0][2] is None: 
            history_query = postgresql.select_data("messages", f"conversation_id = '{request_body.conversation_id}'", 'message_text')
            history = [list(tupla) for tupla in history_query]
            if history:
                generate_topic_tools = GenerateTopicTool()
                topic = generate_topic_tools.generate_topic(history, rows[0][1])
                postgresql.update_data("conversations", f"topic = '{topic}', save_chat = '{request_body.save_chat}', modified_at = '{timestamptz}'", f"conversation_id = '{request_body.conversation_id}' AND user_id = '{request_body.user_id}'")

        
        postgresql.close_connection()
        return func.HttpResponse(status_code=204)

    except Exception as e:
        logging.exception("Exception in SaveConversation")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 


