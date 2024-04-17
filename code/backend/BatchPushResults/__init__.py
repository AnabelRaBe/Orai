import logging, json
import azure.functions as func
from typing import Tuple
from urllib.parse import urlparse
from ..utilities.helpers.ConfigHelper import ConfigHelper
from ..utilities.helpers.DocumentProcessorHelper import DocumentProcessor
from ..utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient


def _get_metadata_from_message(msg: func.EventHubEvent) -> Tuple[str, str, str, dict]:
    message_body = json.loads(msg.get_body().decode('utf-8'))
    filename = message_body.get('filename', "/".join(urlparse(message_body.get('data', {}).get('url', '')).path.split('/')[2:]))
    index_name = message_body.get('index_name')
    container_name = message_body.get('container_name')
    metadata = json.loads(message_body.get('metadata'))
    return filename, index_name, container_name, metadata


def main(msg: func.EventHubEvent) -> None:
    logging.info('Python queue trigger function processed a queue item: %s', msg.get_body().decode('utf-8'))
    file_name, index_name, container_name, metadata = _get_metadata_from_message(msg)
    document_processor = DocumentProcessor()
    blob_client = AzureBlobStorageClient(container_name=container_name)

    file_sas = blob_client.get_blob_sas(file_name)
    file_extension = file_name.split(".")[-1]

    processors = list(filter(lambda x: x.document_type == file_extension, ConfigHelper.get_active_config_or_default().document_processors))
    document_processor.process(source_url=file_sas, processors=processors, index_name=index_name, metadata=metadata)
    blob_client.upsert_blob_metadata(file_name, {'embeddings_added': 'true'})
