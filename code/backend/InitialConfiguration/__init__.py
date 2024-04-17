import logging
import json
import azure.functions as func
from ..utilities.helpers.ConfigHelper import ConfigHelper
from ..utilities.helpers.AzureBlobStorageHelper import AzureBlobStorageClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Requested to start processing InitialConfiguration')

    CONFIG_CONTAINER_NAME = "config"

    try: 
        blob_client = AzureBlobStorageClient(container_name=CONFIG_CONTAINER_NAME)
        config = blob_client.download_file("active.json")
        return func.HttpResponse(config, status_code=200, mimetype="application/json")
    except Exception as e:
        logging.exception("Exception in InitialConfiguration")
        return func.HttpResponse(json.dumps({"Error": str(e)}), status_code=500, mimetype="application/json") 
