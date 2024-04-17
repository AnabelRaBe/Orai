import os
import json
from datetime import datetime
from ..helpers.AzureSearchHelper import AzureSearchHelper

class ConversationLogger():
    def __init__(self):
        self.logger = AzureSearchHelper(index_name=os.getenv("AZURE_SEARCH_CONVERSATIONS_LOG_INDEX")).get_conversation_logger()
        
    def log(self, messages: list):
        self.log_user_message(messages)
        self.log_assistant_message(messages)
        
    def log_user_message(self, messages: dict):
        text = ""
        metadata = {}
        for message in messages:
            if message['role'] == "user":
                metadata['type'] = message['role']
                metadata['conversation_id'] = message.get('conversation_id')
                metadata['created_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                metadata['updated_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                text = message['content']
        self.logger.add_texts(texts=[text], metadatas=[metadata])                
        
    def log_assistant_message(self, messages: dict):
        text = ""
        metadata = {}
        try:
            metadata['conversation_id'] = set(filter(None, [message.get('conversation_id') for message in messages])).pop()
        except KeyError:
            metadata['conversation_id'] = None
        for message in messages:
            if message['role'] == "assistant":
                metadata['type'] = message['role']
                metadata['created_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                metadata['updated_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                text = message['content']
            elif message['role'] == "tool":
                metadata['sources'] = [source['id'] for source in json.loads(message["content"]).get("citations", [])]
        self.logger.add_texts(texts=[text], metadatas=[metadata])
            