import os
import json
import asyncio
import logging
import azure.functions as func
from dotenv import load_dotenv
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
from ..utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient


def search_metadata_by_file_name(filename:str, list_metadata:list) -> str: 

    metadata = {}

    for file in list_metadata:
        keys = list(file.keys())

        if keys[0] == filename:
            metadata = file[filename]

    return json.dumps(metadata)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to start processing all documents received')
    load_dotenv()

    data = req.get_json()
    user_id = data['user_id']
    is_global_index = data['is_global_index']
    process_all = data['process_all']

    if is_global_index:
        index_name = os.getenv("AZURE_SEARCH_INDEX")
        container_name = os.getenv("AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME")
    else:
        index_name = f"{user_id}-index" 
        container_name = os.getenv("AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME")


    azure_blob_storage_client = AzureBlobStorageClient(container_name=container_name)

    try:
        files_data = azure_blob_storage_client.get_all_files()
        files_data = list(filter(lambda x : not x['embeddings_added'], files_data)) if process_all != True else files_data
        files_data = list(map(lambda x: {'filename': x['filename'],
                                        'index_name': index_name,
                                        'metadata': search_metadata_by_file_name(x['filename'], data['metadata']),
                                        'container_name': container_name}, files_data))
        if files_data:
            producer = EventHubProducerClient.from_connection_string(
                conn_str=os.getenv('EVENT_HUB_CONNECTION_STR'),
                eventhub_name=os.getenv('EVENT_HUB_NAME')
            )
            async with producer:
                event_data_batch = await producer.create_batch()
                for fd in files_data:
                    event_data_batch.add(EventData(json.dumps(fd).encode('utf-8')))
                await producer.send_batch(event_data_batch)

        return func.HttpResponse(f"Conversion started successfully for {len(files_data)} documents.", status_code=200)
    
    except Exception as e:
        logging.exception("Exception in BatchStartProcessing")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json")