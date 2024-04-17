from langchain.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
)
from .LLMHelper import LLMHelper
from .EnvHelper import EnvHelper
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient

class AzureSearchHelper():
    def __init__(self, index_name: str):
        env_helper = EnvHelper()
        self.service_endpoint = env_helper.AZURE_SEARCH_SERVICE
        self.admin_key = env_helper.AZURE_SEARCH_KEY
        self.index_name = index_name

    def check_index_exists(self):
        client = SearchIndexClient(endpoint=self.service_endpoint,
                                   credential=AzureKeyCredential(self.admin_key))
        try:
            client.get_index(name=self.index_name)
            return True
        except Exception as e:
            return False
    
    def get_vector_store(self):
        llm_helper = LLMHelper()
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=len(llm_helper.get_embedding_model().embed_query("Text")),
                vector_search_configuration="default",
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="source",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SimpleField(
                name="chunk",
                type=SearchFieldDataType.Int32,
                filterable=True,
            ),
            SimpleField(
                name="offset",
                type=SearchFieldDataType.Int32,
                filterable=True,
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                filterable=True,
            ),
            SearchableField(
                name="global_business",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="divisions_and_areas",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="tags",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="region",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="country",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="language",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SimpleField(
                name="year",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True, 
            ),
            SearchableField(
                name="period",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SimpleField(
                name="importance",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True, 
            ),
            SearchableField(
                name="security",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="origin",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SearchableField(
                name="domain",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            )
        ]
        
        return AzureSearch(
            azure_search_endpoint=self.service_endpoint,
            azure_search_key=self.admin_key,
            index_name=self.index_name,
            embedding_function=llm_helper.get_embedding_model().embed_query,
            fields=fields,
            user_agent="langchain chatwithyourdata-sa",
        )
    
    def get_conversation_logger(self):
        llm_helper = LLMHelper()
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SimpleField(
                name="conversation_id",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=len(llm_helper.get_embedding_model().embed_query("Text")),
                vector_search_configuration="default",
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
            ),
            SimpleField(
                name="type",
                type=SearchFieldDataType.String,
                facetable=True,
                filterable=True,
            ),
            SimpleField(
                name="user_id",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="sources",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="created_at",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
            ),
            SimpleField(
                name="updated_at",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
            ),
        ]
        
        return AzureSearch(
            azure_search_endpoint=self.service_endpoint,
            azure_search_key=self.admin_key,
            index_name=self.index_name,
            embedding_function=llm_helper.get_embedding_model().embed_query,
            fields=fields,
            user_agent="langchain chatwithyourdata-sa",
        )
    