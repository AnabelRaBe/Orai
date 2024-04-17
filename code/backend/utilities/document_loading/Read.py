from typing import List
from .DocumentLoadingBase import DocumentLoadingBase
from ..helpers.AzureFormRecognizerHelper import AzureFormRecognizerClient
from ..common.SourceDocument import SourceDocument

class ReadDocumentLoading(DocumentLoadingBase):
    def __init__(self) -> None:
        super().__init__()
    
    def load(self, document_url: str, metadata: dict) -> List[SourceDocument]:
        azure_form_recognizer_client = AzureFormRecognizerClient()
        pages_content = azure_form_recognizer_client.begin_analyze_document_from_url(document_url, use_layout=False)        
        documents = [
            SourceDocument(
                content=page['page_text'],
                source=document_url,
                page_number=page['page_number'],
                offset=page['offset'],
                global_business=metadata["global_business"],
                divisions_and_areas=metadata["divisions_and_areas"],
                tags=', '.join(metadata["tags"]),
                region=metadata["region"],
                country=metadata["country"],
                language=metadata["language"],
                year=metadata["year"],
                period=metadata["period"],
                importance=metadata["importance"],
                security=metadata["security"],
                origin=metadata["origin"],
                domain=metadata["domain"]
            )
            for page in pages_content
        ]
        return documents
    