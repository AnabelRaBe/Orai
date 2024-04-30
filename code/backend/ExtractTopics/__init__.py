import logging
import json
import azure.functions as func
from ..utilities.common.PostgreSQL import PostgreSQL
from ..utilities.common.ValidationRequest import RequestTopic
from dotenv import load_dotenv


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to extract topics from conversations')

    load_dotenv()

    try:
        request_body = req.get_json()

        user_id = request_body["user_id"].replace("-index", "")

        postgresql = PostgreSQL()

        topics = postgresql.select_data("conversations", f"user_id = '{user_id}' AND save_chat = 'True' AND topic IS NOT NULL",
                                        'conversation_id, topic, created_at, modified_at')
        topic_json = [
            {
                "conversation_id": str(tupla[0]),
                "topic": tupla[1],
                "created_at": str(tupla[2]),
                "modified_at": str(tupla[3])
            }
            for tupla in topics
            if RequestTopic(conversation_id=tupla[0], topic=tupla[1], created_at=tupla[2], modified_at=tupla[3])
        ]
        
        postgresql.close_connection()
        return func.HttpResponse(body=json.dumps(topic_json), status_code=200)

    except Exception as e:
        logging.exception("Exception in ExtractTopics")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 


