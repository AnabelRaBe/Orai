import logging
import json
import azure.functions as func
from ..utilities.common.PostgreSQL import PostgreSQL
from ..utilities.common.ValidationRequest import RequestHistoricalMessage, Message
from dotenv import load_dotenv

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to get historical messages')

    load_dotenv()

    try:

        request_body = req.get_json()
        
        conversation_id = request_body["conversation_id"]

        postgresql = PostgreSQL()

        messages = postgresql.select_data("messages", f"conversation_id = '{conversation_id}'",
                                        'id_message, message_text, created_at')

        messages_json = RequestHistoricalMessage(
            messages=[
                Message(
                    id=tupla[0],
                    author=tupla[1]['author'],
                    content=tupla[1]['content'],
                    datetime=tupla[2].isoformat()
                ) for tupla in messages
            ]
        )

        postgresql.close_connection()
        return func.HttpResponse(body=messages_json.model_dump_json(), status_code=200)

    except Exception as e:
        logging.exception("Exception in GetHistoricalMessages")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 


