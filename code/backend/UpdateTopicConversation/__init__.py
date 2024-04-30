import logging
import datetime
import json
import azure.functions as func
from ..utilities.common.PostgreSQL import PostgreSQL
from ..utilities.common.ValidationRequest import RequestUpdateTopic
from dotenv import load_dotenv


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    load_dotenv()

    try:
        request_body = req.get_json()
        validated_body = RequestUpdateTopic(**request_body)

        postgresql = PostgreSQL()
        now = datetime.datetime.now()
        timestamptz = now.isoformat()

        postgresql.update_data("conversations", f"topic = '{validated_body.topic}', modified_at = '{timestamptz}'",
                                f"conversation_id = '{validated_body.conversation_id}' AND user_id = '{validated_body.user_id}'")
        
        postgresql.close_connection()
        return func.HttpResponse(status_code=204)
    
    except Exception as e:
        logging.exception("Exception in UpdateTopicConversation")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 

