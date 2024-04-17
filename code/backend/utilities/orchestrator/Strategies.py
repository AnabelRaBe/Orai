from enum import Enum

class OrchestrationStrategy(Enum):
    OPENAI_FUNCTION = 'openai_function'
    LANGCHAIN = 'langchain'

def get_orchestrator(orchestration_strategy: str, language: str,global_index_name: str, user_index_name: str):
    if orchestration_strategy == OrchestrationStrategy.LANGCHAIN.value:
        from .LangChainAgent import LangChainAgent
        return LangChainAgent(language, global_index_name, user_index_name)
    else:
        raise Exception(f"Unknown orchestration strategy: {orchestration_strategy}")