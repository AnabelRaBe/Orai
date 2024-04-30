import logging
import json
import azure.functions as func
from ..utilities.common.PostgreSQL import PostgreSQL
from ..utilities.common.ValidationRequest import RequestDelete
from dotenv import load_dotenv


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to delete conversation')

    load_dotenv()

    try:
        request_body = req.get_json()

        validated_body = RequestDelete(**request_body)

        postgresql = PostgreSQL()
        save_chat = postgresql.select_data("conversations", f"conversation_id = '{validated_body.conversation_id}'", 'save_chat')

        if validated_body.delete or (validated_body.new_conversation and not save_chat[0][0]):
            postgresql.delete_data("conversations", f"conversation_id = '{validated_body.conversation_id}'")
            postgresql.delete_data("message_store", f"session_id = '{validated_body.conversation_id}'")
        
        postgresql.close_connection()

        return func.HttpResponse(status_code=204)
    
    except Exception as e:
        logging.exception("Exception in DeleteConversation")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 
