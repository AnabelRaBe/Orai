import os
import json
import logging
import azure.functions as func
import requests
from dotenv import load_dotenv
from ..utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to start processing the blob file upload.')
    
    load_dotenv()

    user_id = req.form.get('user_id')
    file_name = req.form.get('file_name')
    is_global_index_str = req.form.get('is_global_index', '').lower()
    is_global_index = is_global_index_str == 'true' if is_global_index_str else False
    file_bytes = req.files['file'].read()

    print(file_bytes)


    if is_global_index: 
        file_name = file_name
        container_name = os.getenv("AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME")
    else:
        file_name = f"{user_id}/{file_name}"
        container_name = os.getenv("AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME")

    blob_storage_client = AzureBlobStorageClient(container_name = container_name)

    try:
           
        #blob_storage_client.upload_blob_file(bytes_data = file_bytes, uploaded_file_name = file_name, user_id = user_id)

        return func.HttpResponse(json.dumps({"Success": f"The file {file_name} has been uploaded."}), status_code=200, mimetype="application/json") 
    except Exception as e:
        #logging.exception("Exception in BlobFileUpload")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 
    

