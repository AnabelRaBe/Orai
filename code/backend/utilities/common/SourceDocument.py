from typing import Optional, Type
import hashlib
import json
from urllib.parse import urlparse, quote
from ..helpers.AzureBlobStorageHelper import AzureBlobStorageClient

class SourceDocument:
    def __init__(self, content: str, source: str, id: Optional[str] = None, title: Optional[str] = None,
                 chunk: Optional[int] = None, offset: Optional[int] = None, page_number: Optional[int] = None, container_name: Optional[str] = None, 
                 global_business: Optional[str] = None, divisions_and_areas: Optional[str] = None, tags: Optional[list] = None, region: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, year: Optional[str] = None, period: Optional[str] = None, importance: Optional[str] = None, security: Optional[str] = None, origin: Optional[str] = None, domain: Optional[str] = None):
        self.id = id
        self.content = content
        self.source = source
        self.title = title
        self.chunk = chunk
        self.offset = offset
        self.page_number = page_number
        self.container_name = container_name
        self.global_business = global_business
        self.divisions_and_areas = divisions_and_areas
        self.tags = tags    
        self.region = region
        self.country = country
        self.language = language
        self.year = year
        self.period = period
        self.importance = importance
        self.security = security
        self.origin = origin
        self.domain = domain        
        
    def __str__(self):
        return f"SourceDocument(id={self.id}, title={self.title}, source={self.source}, chunk={self.chunk}, offset={self.offset}, page_number={self.page_number}, container_name={self.container_name}, global_business={self.global_business}, divisions_and_areas={self.divisions_and_areas}, tags ={self.tags}, region={self.region}, country={self.country}, language={self.language}, year={self.year}, period={self.period}, importance={self.importance}, security={self.security}, origin={self.origin}, domain={self.domain})"
    
    def to_json(self):
        return json.dumps(self, cls=SourceDocumentEncoder)
    
    @classmethod
    def from_json(cls, json_string):
        return json.loads(json_string, cls=SourceDocumentDecoder)
    
    @classmethod
    def from_dict(cls, dict_obj):
        return cls(
            dict_obj['id'],
            dict_obj['content'],
            dict_obj['source'],
            dict_obj['title'],
            dict_obj['chunk'],
            dict_obj['offset'],
            dict_obj['page_number'],
            dict_obj['container_name'],
            dict_obj['global_business'],
            dict_obj['divisions_and_areas'],
            dict_obj['tags'],
            dict_obj['region'],
            dict_obj['country'],
            dict_obj['language'],
            dict_obj['year'],
            dict_obj['period'],
            dict_obj['importance'],
            dict_obj['security'],
            dict_obj['origin'],
            dict_obj['domain']
        )
    
    @classmethod
    def from_metadata(
        cls: Type['SourceDocument'],
        content: str,
        metadata: dict,
        document_url: Optional[str],
        idx: Optional[int],
    ) -> 'SourceDocument':   
        parsed_url = urlparse(document_url)
        file_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
        filename = parsed_url.path
        hash_key = hashlib.sha1(f"{file_url}_{idx}".encode("utf-8")).hexdigest()
        hash_key = f"doc_{hash_key}"
        sas_placeholder = "_SAS_TOKEN_PLACEHOLDER_" if 'blob.core.windows.net' in parsed_url.netloc else ""
        return cls(
            id = metadata.get('id', hash_key),
            content = content,
            source = metadata.get('source', f"{file_url}{sas_placeholder}"),
            title = metadata.get('title', filename),
            chunk = metadata.get('chunk', idx),
            offset = metadata.get('offset'),
            page_number = metadata.get('page_number'),
            global_business = metadata.get('global_business'),
            divisions_and_areas = metadata.get('divisions_and_areas'),
            tags = metadata.get('tags'),
            region = metadata.get('region'),
            country = metadata.get('country'),
            language = metadata.get('language'),
            year = metadata.get('year'),
            period = metadata.get('period'),
            importance = metadata.get('importance'),
            security = metadata.get('security'),
            origin = metadata.get('origin'),
            domain = metadata.get('domain')
        )
    
    def convert_to_langchain_document(self):
        from langchain.docstore.document import Document
        return Document(
            page_content=self.content,
            metadata={
                "id": self.id,
                "source": self.source,
                "title": self.title,
                "chunk": self.chunk,
                "offset": self.offset,
                "page_number": self.page_number,
                "global_business": self.global_business,
                "divisions_and_areas": self.divisions_and_areas,
                "tags": self.tags,
                "region": self.region,
                "country": self.country,
                "language": self.language,
                "year": self.year,
                "period": self.period,
                "importance": self.importance,
                "security": self.security,
                "origin": self.origin,
                "domain": self.domain
            }
        )
        
    def get_filename(self, include_path=False):
        filename = self.source.replace('_SAS_TOKEN_PLACEHOLDER_', '').replace('http://', '')
        if include_path:
            filename = filename.split('/')[-1]
        else:
            filename = filename.split('/')[-1].split('.')[0]
        return filename
    
    def get_markdown_url(self):
        url = quote(self.source, safe=':/')
        if '_SAS_TOKEN_PLACEHOLDER_' in url:
            blob_client = AzureBlobStorageClient(container_name=self.container_name)
            container_sas = blob_client.get_container_sas()
            url = url.replace("_SAS_TOKEN_PLACEHOLDER_", container_sas)
        return f"[{self.title}]({url}#page={self.page_number+1})"
        
class SourceDocumentEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SourceDocument):
            return {
                'id': obj.id,
                'content': obj.content,
                'source': obj.source,
                'title': obj.title,
                'chunk': obj.chunk,
                'offset': obj.offset,
                'page_number': obj.page_number,
                "container_name": obj.container_name,
                "global_business": obj.global_business,
                "divisions_and_areas": obj.divisions_and_areas,
                "tags": obj.tags,
                "region": obj.region,
                "country": obj.country,
                "language": obj.language,
                "year": obj.year,
                "period": obj.period,
                "importance": obj.importance,
                "security": obj.security,
                "origin": obj.origin,
                "domain": obj.domain
            }
        return super().default(obj)
    
class SourceDocumentDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        obj = super().decode(s, **kwargs)
        return SourceDocument(
            id=obj['id'],
            content=obj['content'],
            source=obj['source'],
            title=obj['title'],
            chunk=obj['chunk'],
            offset=obj['offset'],
            page_number=obj['page_number'],
            container_name=obj['container_name'],
            global_business=obj['global_business'],
            divisions_and_areas=obj['divisions_and_areas'],
            tags=obj['tags'],
            region=obj['region'],
            country=obj['country'],
            language=obj['language'],
            year=obj['year'],
            period=obj['period'],
            importance=obj['importance'],
            security=obj['security'],
            origin=obj['origin'],
            domain=obj['domain']
        )