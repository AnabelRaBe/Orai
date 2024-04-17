from typing import List
from .AnsweringToolBase import AnsweringToolBase
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from ..helpers.LLMHelper import LLMHelper
from ..common.Answer import Answer


class FAQTool(AnsweringToolBase):

    def __init__(self, config: dict) -> None:
        self.config = config
        self.verbose = True
    
    def answer_question(self, question: str, chat_history: List[dict], **kwargs: dict) -> Answer:
        faq_prompt = PromptTemplate(template=self.config.prompts.faq_answering_prompt, input_variables=["content", "question", "max_followups_questions"])
        llm_helper = LLMHelper()
        answer_generator = LLMChain(llm=llm_helper.get_llm(self.config.llm.model, self.config.llm.temperature, self.config.llm.max_tokens), prompt=faq_prompt, verbose=self.verbose)
        content = self.config.prompts.faq_content

        with get_openai_callback() as cb:
            result = answer_generator({"content": content,
                                       "question": question,
                                       "max_followups_questions": self.config.llm.max_followups_questions})
        
        answer = result["text"]

        clean_answer = Answer(question=question,
                              answer=answer,
                              source_documents=[],
                              prompt_tokens=cb.prompt_tokens,
                              completion_tokens=cb.completion_tokens)
        return clean_answer
