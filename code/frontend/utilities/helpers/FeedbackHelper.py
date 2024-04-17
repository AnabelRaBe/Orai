import json
from typing import Optional
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from .AzureBlobStorageHelper import AzureBlobStorageClient
from .EnvHelper import EnvHelper

class Feedback:
    def __init__(self, user_id: str, name: str, feedback: dict, question: str, answer: str, citations: list, conversation_id: str, config_LLM: dict, prompt: str, account_name: Optional[str] = None, account_key: Optional[str] = None, container_name: Optional[str] = None):
        env_helper : EnvHelper = EnvHelper()

        self.user_id : str = user_id
        self.name : str = name
        self.feedback: dict = feedback
        self.question : str = question
        self.answer : str = answer
        self.citations : str = citations
        self.conversation_id : str = conversation_id
        self.config_LLM: dict = config_LLM
        self.prompt : str = prompt
        self.account_name : str = account_name if account_name else env_helper.AZURE_BLOB_ACCOUNT_NAME
        self.account_key : str = account_key if account_key else env_helper.AZURE_BLOB_ACCOUNT_KEY
        self.container_name : str = container_name if container_name else env_helper.AZURE_BLOB_CONTAINER_FEEDBACK_NAME
        self.blob_storage_client : AzureBlobStorageClient = AzureBlobStorageClient(account_name=self.account_name, account_key=self.account_key, container_name=self.container_name)

    def generate_json_feedback(self):
        
        now = datetime.now()

        data = {
            "user_id": self.user_id,
            "name": self.name, 
            "date": now.strftime("%Y-%m-%d_%H-%M-%S"),
            "conversation_id": self.conversation_id,
            "feedback": self.feedback,
            "question": self.question,
            "prompt": self.prompt,
            "answer": self.answer,
            "citations": self.citations,
            "format_feedback": {"messages": [{"role": "system", "content": self.answer }, {"role": "user", "content": self.question}]},
            "model_configuration": self.config_LLM 
        }
        
        data_json = json.dumps(data, indent=2)
        blob_name = now.strftime("%Y-%m-%d_%H-%M-%S_feedback_" + self.conversation_id)

        self.blob_storage_client.prepare_blob(self.user_id, data_json, blob_name)
