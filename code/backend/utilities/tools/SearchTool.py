import os
from typing import List
from datetime import datetime
from .AnsweringToolBase import AnsweringToolBase
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from ..common.Answer import Answer
from ..helpers.LLMHelper import LLMHelper
from ..common.SourceDocument import SourceDocument
from ..helpers.AzureSearchHelper import AzureSearchHelper
 
 
class SearchTool(AnsweringToolBase):
    def __init__(self, global_index_name: str, user_index_name: str, config: dict) -> None:
        self.global_index_name = global_index_name
        self.global_vector_store = AzureSearchHelper(self.global_index_name).get_vector_store()
        self.user_index_name = user_index_name
        if self.user_index_name:
            self.azure_search_client = AzureSearchHelper(index_name=user_index_name)
            self.user_index_exists = False
            if self.azure_search_client.check_index_exists():
                self.user_index_exists = True
                self.user_vector_store = AzureSearchHelper(self.user_index_name).get_vector_store()
        self.verbose = True
        self.config = config
    
    def answer_question(self, question: str, chat_history: List[dict], **kwargs: dict) -> Answer:
        answering_prompt = PromptTemplate(template=self.config.prompts.answering_prompt,
                                          input_variables=["question", "sources", "current_date", "max_followups_questions"])
        # answering_prompt = PromptTemplate(template="Context:\n{sources}\nQuestion:\n{question}\n",
        #                                   input_variables=["question", "sources", "current_date", "max_followups_questions"])
        
        global_sources = self.global_vector_store.similarity_search(query=question, k=5, search_type="hybrid")
        global_sources_text = "\n\n".join([f"[doc{i+1}]: {source.page_content}" for i, source in enumerate(global_sources)])
 
        if self.user_index_exists:
            user_sources = self.user_vector_store.similarity_search(query=question, k=5, search_type="hybrid")
            user_sources_text = "\n\n".join([f"[doc{len(global_sources)+i+1}]: {source.page_content}" for i, source in enumerate(user_sources)])
            global_sources_text += "\n\n" + user_sources_text
 
        llm_helper = LLMHelper()
        answer_generator = LLMChain(llm=llm_helper.get_llm(self.config.llm.model, self.config.llm.temperature, self.config.llm.max_tokens), prompt=answering_prompt, verbose=self.verbose)
 
        with get_openai_callback() as cb:
            result = answer_generator({"question": question,
                                       "sources": global_sources_text,
                                       "current_date": datetime.today().strftime('%Y-%m-%d'),
                                       "max_followups_questions": self.config.llm.max_followups_questions})
        
        answer = result["text"]
 
        source_documents = []
        for source in global_sources:
            global_source_document = SourceDocument(
                id=source.metadata["id"],
                content=source.page_content,
                title=source.metadata["title"],
                source=source.metadata["source"],
                chunk=source.metadata["chunk"],
                offset=source.metadata["offset"],
                page_number=source.metadata["page_number"],
                container_name=os.getenv('AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME'),
            )
            source_documents.append(global_source_document)
        
        if self.azure_search_client.check_index_exists():
            for source in user_sources:
                local_source_document = SourceDocument(
                    id=source.metadata["id"],
                    content=source.page_content,
                    title=source.metadata["title"],
                    source=source.metadata["source"],
                    chunk=source.metadata["chunk"],
                    offset=source.metadata["offset"],
                    page_number=source.metadata["page_number"],
                    container_name=os.getenv('AZURE_BLOB_LOCAL_DOCUMENTS_CONTAINER_NAME'),
                )
                source_documents.append(local_source_document)
        
        clean_answer = Answer(question=question,
                              answer=answer,
                              source_documents=source_documents,
                              prompt_tokens=cb.prompt_tokens,
                              completion_tokens=cb.completion_tokens)
        return clean_answer