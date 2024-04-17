import json
from typing import Optional
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from .AzureBlobStorageHelper import AzureBlobStorageClient
from .EnvHelper import EnvHelper
import regex as re
from utilities.tools.GenerateTopicTool import GenerateTopicTool

class Conversation:
    def __init__(self, user_id: str, conversation_id: str, account_name: Optional[str] = None, account_key: Optional[str] = None, container_name: Optional[str] = None):
        env_helper : EnvHelper = EnvHelper()

        self.user_id : str = user_id
        self.conversation_id : str = conversation_id
        self.account_name : str = account_name if account_name else env_helper.AZURE_BLOB_ACCOUNT_NAME
        self.account_key : str = account_key if account_key else env_helper.AZURE_BLOB_ACCOUNT_KEY
        self.container_name : str = container_name if container_name else env_helper.AZURE_BLOB_CONTAINER_CONVERSATIONS_NAME
        self.blob_storage_client : AzureBlobStorageClient = AzureBlobStorageClient(account_name=self.account_name, account_key=self.account_key, container_name=self.container_name)
    
    def prepare_conversation_txt(self, json_bytes: bytes) -> str:
        conversation = ""
        conversation += f"Last date: {self.date_format(json_bytes)}\n\n"
        conversation += f"\n----------------------------------------------------------------------------\n"
        conversation += f"{json.loads(json_bytes)['topic']}"
        conversation += f"\n----------------------------------------------------------------------------\n\n"

        conversation += "\n......................................\nConversation\n......................................\n\n"
        for message in json.loads(json_bytes)["langchain"]["messages"]:
            if message["role"] in ["user", "assistant"]:
                conversation += f"{message['role'].capitalize()}: {message['content']}\n\n"

        conversation = self.delete_followup_questions_txt(conversation)

        return conversation
    
    def delete_followup_questions_txt(self, conversation: str) -> str:
        pattern = re.compile(r'<<.*?>>')
        result = pattern.sub('', conversation)
        
        return result
    
    def date_format(self, json_bytes: bytes) -> str:
        date_chain = json.loads(json_bytes)["modified_date"]
        date_separated = date_chain.split("_")
    
        day = date_separated[0]
        day_list = day.split("-")
        day_final = "-".join([day_list[2], day_list[1], day_list[0]])
    
        hour = date_separated[1]
        hour_format = hour.replace("-", ":")
        hour_final = hour_format.replace("/", "")
    
        date = " ".join([day_final, hour_final])
        return date

    def generate_json_historical_conversation(self, language, chat_history_langchain, chat_history, chat_source_documents, chat_source_document_preview, conversation_sources_url, chat_askedquestion, chat_question, chat_followup_questions, input_message_key, collected_historical_conversation, conversation_init_date, conversation_file_name, conversation_topic) -> bool:
        azure_blob_client = AzureBlobStorageClient(account_name=self.account_name, account_key=self.account_key, container_name=self.container_name)
        generate_topic_tools = GenerateTopicTool()
        now = datetime.now()

        if collected_historical_conversation:
            azure_blob_client.delete_file(conversation_file_name)
            collected_historical_conversation = False
            date = conversation_init_date
        else: 
            date = now.strftime("%Y-%m-%d_%H-%M-%S")

        if conversation_topic == "":
            topic = generate_topic_tools.generate_topic(chat_history, language)
        else:
            topic = conversation_topic

        data = {
            "user_id": self.user_id,
            "init_date": date,
            "topic": topic,
            "modified_date": now.strftime("%Y-%m-%d_%H-%M-%S"),
            "langchain": chat_history_langchain,
            "history": chat_history,
            "documents": chat_source_documents,
            "document_preview": chat_source_document_preview,
            "sources_url": conversation_sources_url,
            "askedquestion": chat_askedquestion,
            "chat_question": chat_question,
            "followup_questions": chat_followup_questions,
            "conversation_id": self.conversation_id,
            "input_message_key": input_message_key
        }
        data_json = json.dumps(data, indent=2)
        blob_name = now.strftime(f"conversation_%Y-%m-%d_%H-%M-%S")

        self.blob_storage_client.prepare_blob(self.user_id, data_json, blob_name)

        return collected_historical_conversation

    def edit_topic_historical_conversation(self, file: str, json_bytes: bytes, new_topic: str):
        now = datetime.now()

        data = {
            "user_id": self.user_id,
            "init_date": json.loads(json_bytes)["init_date"],
            "topic": new_topic,
            "modified_date": now.strftime("%Y-%m-%d_%H-%M-%S"),
            "langchain": json.loads(json_bytes)["langchain"],
            "history": json.loads(json_bytes)["history"],
            "documents": json.loads(json_bytes)["documents"],
            "document_preview": json.loads(json_bytes)["document_preview"],
            "sources_url": json.loads(json_bytes)["sources_url"],
            "askedquestion": json.loads(json_bytes)["askedquestion"],
            "chat_question": json.loads(json_bytes)["chat_question"],
            "followup_questions": json.loads(json_bytes)["followup_questions"],
            "conversation_id": json.loads(json_bytes)["conversation_id"],
            "input_message_key": json.loads(json_bytes)["input_message_key"]
        }
        data_json = json.dumps(data, indent=2)
        blob_name = now.strftime("conversation_%Y-%m-%d_%H-%M-%S")

        self.blob_storage_client.delete_file(file)

        self.blob_storage_client.prepare_blob(self.user_id, data_json, blob_name)

    def get_files_stored_chronological(self) -> list:

        files_stored = self.blob_storage_client.get_all_files_by_user_id(self.user_id)
        files_stored_chronological = files_stored[::-1]

        return files_stored_chronological




    