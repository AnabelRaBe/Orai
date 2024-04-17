import os
import json
import mimetypes
import chardet
from os import remove
from typing import Optional
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, generate_container_sas, ContentSettings
from .EnvHelper import EnvHelper

class AzureBlobStorageClient:
    def __init__(self, account_name: Optional[str] = None, account_key: Optional[str] = None, container_name: Optional[str] = None):

        env_helper : EnvHelper = EnvHelper()

        self.account_name = account_name if account_name else env_helper.AZURE_BLOB_ACCOUNT_NAME
        self.account_key = account_key if account_key else env_helper.AZURE_BLOB_ACCOUNT_KEY
        self.connect_str = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.account_key};EndpointSuffix=core.windows.net"
        self.container_name : str = container_name if container_name else env_helper.AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME
        self.blob_service_client : BlobServiceClient = BlobServiceClient.from_connection_string(self.connect_str)

    def upload_file(self, bytes_data, file_name, content_type='application/pdf'):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        blob_client.upload_blob(bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
        return blob_client.url + '?' + generate_blob_sas(self.account_name, self.container_name, file_name,account_key=self.account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))

    def download_file(self, file_name):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        return blob_client.download_blob().readall()
    
    def delete_file(self, file_name):
        """
        Deletes a file from the Azure Blob Storage container.

        Args:
            file_name (str): The name of the file to delete.

        Returns:
            None
        """
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        blob_client.delete_blob()

    def get_all_files_feedback(self, container_name: str) -> list:
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs()
        feedbacks = []
        for blob in blob_list:
            feedback = self.download_file(blob.name)
            feedbacks.append(json.loads(feedback))

        return feedbacks

    def get_all_files(self):
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_list = container_client.list_blobs(include='metadata')
        sas = generate_container_sas(self.account_name, self.container_name,account_key=self.account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))
        files = []
        converted_files = {}
        for blob in blob_list:
            if not blob.name.startswith('converted/'):
                files.append({
                    "filename" : blob.name,
                    "converted": blob.metadata.get('converted', 'false') == 'true' if blob.metadata else False,
                    "embeddings_added": blob.metadata.get('embeddings_added', 'false') == 'true' if blob.metadata else False,
                    "fullpath": f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}?{sas}",
                    "converted_filename": blob.metadata.get('converted_filename', '') if blob.metadata else '',
                    "converted_path": ""
                    })
            else:
                converted_files[blob.name] = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}?{sas}"

        for file in files:
            converted_filename = file.pop('converted_filename', '')
            if converted_filename in converted_files:
                file['converted'] = True
                file['converted_path'] = converted_files[converted_filename]
        
        return files

    def get_all_files_by_user_id(self, user_id: str) -> list:
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_list = container_client.walk_blobs(f"{user_id}/", delimiter='/') 
        files = []

        for blob in blob_list: 
            blobs_in_blob = container_client.walk_blobs(name_starts_with=blob.name, delimiter='/')
            for file in blobs_in_blob:
                files.append(file.name)

        return files
    
    def upsert_blob_metadata(self, file_name, metadata):
        blob_client = BlobServiceClient.from_connection_string(self.connect_str).get_blob_client(container=self.container_name, blob=file_name)
        blob_metadata = blob_client.get_blob_properties().metadata
        blob_metadata.update(metadata)
        blob_client.set_blob_metadata(metadata= blob_metadata)

    def get_container_sas(self):
        return "?" + generate_container_sas(account_name= self.account_name, container_name= self.container_name,account_key=self.account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=1))

    def get_blob_sas(self, file_name):
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{file_name}" + "?" + generate_blob_sas(account_name= self.account_name, container_name=self.container_name, blob_name= file_name, account_key= self.account_key, permission='r', expiry=datetime.utcnow() + timedelta(hours=1))
    
    def prepare_blob(self, user_id: str, data_json: str, blob_name: str):
        now = datetime.now()

        parent_folder_name = user_id
        subfolder_name = now.strftime("%Y-%m-%d_%H-%M-%S")

        parent_folder_blob_name = parent_folder_name + '/'
        subfolder_blob_name = parent_folder_blob_name + subfolder_name + '/'

        file_path = f"{blob_name}"
        file_blob_name = subfolder_blob_name + file_path

        with open(file_path, "w") as json_file:
            json_file.write(data_json)

        self.upload_json_to_azure_storage_account(file_blob_name, file_path)

        remove(file_path)


    def upload_json_to_azure_storage_account(self, file_blob_name: str, file_path: str):
        blob_service_client = BlobServiceClient(account_url=f"https://{self.account_name}.blob.core.windows.net", credential=self.account_key)

        container_client = blob_service_client.get_container_client(self.container_name)

        blob_client = container_client.get_blob_client(file_blob_name + ".json")
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
    
    def upload_blob_file(self, bytes_data: bytes, uploaded_file_name: str, content_type: Optional[str] = None, user_id: Optional[str] = None):     

        if content_type == None:
            content_type = mimetypes.MimeTypes().guess_type(uploaded_file_name)[0]
            charset = f"; charset={chardet.detect(bytes_data)['encoding']}" if content_type == 'text/plain' else ''
            content_type = content_type if content_type != None else 'text/plain'
        
        if self.account_name == None or self.account_key == None or self.container_name == None:
            raise ValueError("Please provide values for AZURE_BLOB_ACCOUNT_NAME, AZURE_BLOB_ACCOUNT_KEY and AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME or AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME")
        
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.account_key};EndpointSuffix=core.windows.net"
        blob_service_client : BlobServiceClient = BlobServiceClient.from_connection_string(connect_str)
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=uploaded_file_name)
        blob_client.upload_blob(bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type+charset))
        
        file_url = blob_client.url + '?' + generate_blob_sas(self.account_name, self.container_name, uploaded_file_name,account_key=self.account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))