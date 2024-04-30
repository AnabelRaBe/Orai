import openai
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from ..helpers.LLMHelper import LLMHelper
from ..helpers.EnvHelper import EnvHelper
from ..helpers.ConfigHelper import ConfigHelper
import time


class GenerateTopicTool():
    def __init__(self):
        env_helper: EnvHelper = EnvHelper()

        openai.api_type = "azure"
        openai.api_version = env_helper.AZURE_OPENAI_API_VERSION
        openai.api_base = env_helper.OPENAI_API_BASE
        openai.api_key = env_helper.OPENAI_API_KEY

        self.verbose = True

    def generate_topic(self, content: str, language: str) -> str:
        llm_helper = LLMHelper()
        config = ConfigHelper.get_active_config_or_default()
        topic_prompt_template="""
        Content: {content}
        Please generate based on the content its summary. After generating the summary, try to find out what is the main topic of the conversation based on the summary.
        Try to be very brief when you are generating the main topic. 
        Only generate and return the main topic and do not generate any text before or after the main topic, such as 'The main topic of the conversation is'. Always must be translated to {language}.
        Begin!

        Answer: 
        """
        
        topic_prompt = PromptTemplate(template=topic_prompt_template, input_variables=["content", "language"])
        topic_generator = LLMChain(llm=llm_helper.get_llm(config.llm.model, config.llm.temperature, config.llm.max_tokens),
                                   prompt=topic_prompt,
                                   verbose=self.verbose)

        with get_openai_callback() as cb:
            result = topic_generator({"content": content, "language": language})

        topic = result["text"]
        (f"Answer: {topic}")
        return topic