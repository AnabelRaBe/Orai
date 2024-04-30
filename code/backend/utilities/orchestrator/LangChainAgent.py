from typing import List
from langchain.chains import LLMChain
from langchain.agents import Tool
from langchain.callbacks import get_openai_callback
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory, PostgresChatMessageHistory
from langchain.agents import ZeroShotAgent, AgentExecutor
from ..common.Answer import Answer
from ..tools.FAQTool import FAQTool
from ..helpers.LLMHelper import LLMHelper
from .OrchestratorBase import OrchestratorBase
from ..tools.PostPromptTool import PostPromptTool
from ..parser.OutputParserTool import OutputParserTool
from ..tools.QuestionAnswerTool import QuestionAnswerTool
from ..tools.SearchTool import SearchTool
import logging, time
import psycopg
import uuid


class LangChainAgent(OrchestratorBase):

    def __init__(self, language: str,global_index_name: str, user_index_name: str):
        super().__init__()

        self.global_index_name = global_index_name
        self.language = language
        self.user_index_name = user_index_name

    def run_search_qna_tool(self, user_message):
        user_message = user_message + ". Using this language: " + self.language
        logging.info("Estoy en run_search_qna_tool")
        time.sleep(5)
        answer = self.search_question_answer_tool.answer_question(user_message, chat_history=[])
        return answer.to_json()    

    def run_global_qna_tool(self, user_message):
        user_message = user_message + ". Using this language: " + self.language
        answer = self.global_question_answer_tool.answer_question(user_message, chat_history=[])
        return answer.to_json()

    def run_faq_qna_tool(self, user_message):
        user_message = user_message + ". Using this language: " + self.language
        answer = self.faq_question_answer_tool.answer_question(user_message, chat_history=[])
        return answer.to_json()
    
    def orchestrate(self, user_message: str, chat_history: List[dict], conversation_id: str, config: dict,  **kwargs: dict) -> dict:
        
        #self.global_question_answer_tool = QuestionAnswerTool(global_index_name=self.global_index_name,
        #                                                      user_index_name=self.user_index_name,
        #                                                      config=config)
        
        self.faq_question_answer_tool = FAQTool(config=config)

        self.search_question_answer_tool = SearchTool(global_index_name=self.global_index_name,
                                                              user_index_name=self.user_index_name,
                                                              config=config)

        self.tools = [
            Tool(
                name="Search and Summary",
                func=self.run_search_qna_tool,
                description="useful for searching and summarizing documents in the knowledge base",
                return_direct=True,
            ),
            Tool(
                name="Basic Question Answering",
                func=self.run_faq_qna_tool,
                #description="useful for when you need to answer basic questions about your identity and the kind of assistance you can provide such as, What's your name?, What kind of things can you do?, What is a chatbot?, What kind of topics can I discuss with Orai? How to ask effective questions? etc.",
                #description = "Use it only when the questions are basic and ask about your identity as an attendee or questions not related to Santander. For example: What is your name? What kind of things can you do? What is a chatbot? What kind of topics can I discuss? with orai? How to ask effective questions? What day is today? etc",
                #description = "Use it only when the questions are basic and ask about your identity as an attendee. For example: What is your name? What kind of things can you do? What is a chatbot? What kind of topics can I discuss? with orai? How to ask effective questions? etc",
                description = "Use it only when the questions are about Orai. For example: What is your name? What kind of things can you do? What is a chatbot? What kind of topics can I discuss? with orai? How to ask effective questions? etc",
                return_direct=True,
            ),
            #Tool(
            #    name="Question Answering",
            #    func=self.run_global_qna_tool,
            #    description="useful for when you need to answer questions that require a more complex answer such as, What are the group's main financial objectives for 2025?, Can you explain the meaning of 'Think Value, Think?' Client, Think Global'?, Summarize and analyze the main variables of the group's financial results in the first half of 2023, What is the mission and vision of Santander?, What is the bank's contribution to society in terms of education?. Useful for searching and summarizing documents in the knowledge base.",
            #    return_direct=True,
            #)
            #,
        ]

        output_formatter = OutputParserTool()

        llm_helper = LLMHelper()
        prefix = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
        suffix = """Begin!"

        {chat_history}
        Question: {input}
        {agent_scratchpad}"""
        prompt = ZeroShotAgent.create_prompt(
            self.tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad"],
        )
        

        conn_info = "postgresql://pfsadmin:d6t7M051Y-km@innd1weupfsportalcrit001.postgres.database.azure.com:5432/chat_history"

        session_id = conversation_id

        chat_history = PostgresChatMessageHistory(
            connection_string = conn_info,
            session_id = session_id,
        )

        memory = ConversationBufferWindowMemory(chat_memory=chat_history,
                                                memory_key="chat_history",
                                                return_messages=True,
                                                k=5)

        llm_chain = LLMChain(llm=llm_helper.get_llm(config.llm.model, config.llm.temperature, config.llm.max_tokens), prompt=prompt)

        agent = ZeroShotAgent(llm_chain=llm_chain, tools=self.tools, verbose=True)
        agent_chain = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=self.tools, verbose=True, memory=memory
        )

        with get_openai_callback() as cb:
            try:
                answer = agent_chain.run(user_message)
                self.log_tokens(prompt_tokens=cb.prompt_tokens, completion_tokens=cb.completion_tokens)
            except Exception as e:
                answer = str(e)
        try:
            answer = Answer.from_json(answer)
        except:
            answer = Answer(question=user_message, answer=answer)
        
        if config.prompts.enable_post_answering_prompt:
            post_prompt_tool = PostPromptTool(config=config)
            answer = post_prompt_tool.validate_answer(answer)
            self.log_tokens(prompt_tokens=answer.prompt_tokens, completion_tokens=answer.completion_tokens)                

        messages = output_formatter.parse(question=answer.question, answer=answer.answer, source_documents=answer.source_documents)  
        return messages
    