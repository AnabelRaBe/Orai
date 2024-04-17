from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from ..common.Answer import Answer
from ..helpers.LLMHelper import LLMHelper


class PostPromptTool():
    def __init__(self, config: dict) -> None:
        self.config = config
    
    def validate_answer(self, answer: Answer) -> dict:
        llm_helper = LLMHelper()
        
        was_message_filtered = False
        post_answering_prompt = PromptTemplate(template=self.config.prompts.post_answering_prompt, input_variables=["question", "answer", "sources"])
        post_answering_chain = LLMChain(llm=llm_helper.get_llm(self.config.llm.model, self.config.llm.temperature, self.config.llm.max_tokens), prompt=post_answering_prompt, output_key="correct", verbose=True)

        sources = '\n'.join([f"[doc{i+1}]: {source.content}" for i, source in enumerate(answer.source_documents)])
    
        with get_openai_callback() as cb:
            post_result = post_answering_chain({"question": answer.question, "answer": answer.answer, "sources": sources})
        
        was_message_filtered = not (post_result['correct'].lower() == 'true' or post_result['correct'].lower() == 'yes')

        if was_message_filtered:
            return Answer(question=answer.question, 
                          answer=self.config.messages.post_answering_filter,
                          source_documents=[],
                          prompt_tokens=cb.prompt_tokens,
                          completion_tokens=cb.completion_tokens)
        else:
            return Answer(question=answer.question, 
                          answer=answer.answer,
                          source_documents=answer.source_documents,
                          prompt_tokens=cb.prompt_tokens,
                          completion_tokens=cb.completion_tokens)
    