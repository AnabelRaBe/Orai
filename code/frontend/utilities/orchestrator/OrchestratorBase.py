# Create an abstract class for orchestrator
from uuid import uuid4
from typing import List, Optional
from abc import ABC, abstractmethod
from ..loggers.TokenLogger import TokenLogger

class OrchestratorBase(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.message_id = str(uuid4())
        self.tokens = {
            'prompt': 0,
            'completion': 0,
            'total': 0
        }
        self.token_logger : TokenLogger = TokenLogger()
    
    def log_tokens(self, prompt_tokens, completion_tokens):
        self.tokens['prompt'] += prompt_tokens
        self.tokens['completion'] += completion_tokens
        self.tokens['total'] += prompt_tokens + completion_tokens
        
    @abstractmethod
    def orchestrate(self, user_message: str, chat_history: List[dict], config: dict, **kwargs: dict) -> dict:
        pass
    
    def handle_message(self, user_message: str, chat_history: List[dict], conversation_id: Optional[str], config: dict, **kwargs: Optional[dict]) -> dict:
        result = self.orchestrate(user_message, chat_history, config, **kwargs)
        if config.logging.log_tokens:
            custom_dimensions = {
                "conversation_id": conversation_id,
                "message_id": self.message_id,
                "prompt_tokens": self.tokens['prompt'],
                "completion_tokens": self.tokens['completion'],
                "total_tokens": self.tokens['total']
            }
            self.token_logger.log("Conversation", custom_dimensions=custom_dimensions)
        return result
        