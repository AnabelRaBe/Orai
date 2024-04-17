import logging
import azure.functions as func
from dotenv import load_dotenv
import os
import json
from utilities.helpers.FeedbackHelper import Feedback


def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Requested to start processing FeedbackStorage')

    load_dotenv()

    try:
        input = req.get_json()
        feedback_object = Feedback(user_id=input['user_id'], 
                                    name=input['name'],
                                    feedback=input['feedback'], 
                                    question=input['question'], 
                                    answer=input['answer'], 
                                    citations=input['citations'], 
                                    conversation_id=input['conversation_id'], 
                                    config_LLM=input['config_LLM'], 
                                    prompt=input['answering_prompt'], 
                                    account_name=os.getenv("AZURE_BLOB_ACCOUNT_NAME"), 
                                    account_key=os.getenv("AZURE_BLOB_ACCOUNT_KEY"), 
                                    container_name=os.getenv("AZURE_BLOB_CONTAINER_FEEDBACK_NAME")
                                    )
        feedback_object.generate_json_feedback()
        return func.HttpResponse(status_code=204)

    except Exception as e:
        logging.exception("Exception in FeedbackStorage")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 


