from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import isodate
from datetime import datetime
from pydantic import BaseModel, ValidationError, field_validator


class RequestSave(BaseModel):
    conversation_id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str = None
    save_chat: bool = False
    language: str = 'Spanish'
    message: list = []

    @field_validator('user_name')
    def validate_user_name(cls, value, values):
        if value is not None and (not value.isdigit() or len(value) > 200):
            raise ValueError("User name must be numeric and have a maximum of 200 characters")
        return value

class RequestDelete(BaseModel):
    delete: bool = False
    new_conversation: bool = False
    conversation_id: uuid.UUID

class Message(BaseModel):
    id: int
    author: str
    content: str
    datetime: datetime

class RequestHistoricalMessage(BaseModel):
    messages: List[Message]

class RequestTopic(BaseModel):
    conversation_id: uuid.UUID
    topic: str
    created_at: datetime
    modified_at: datetime

class RequestUpdateTopic(BaseModel):
    topic: str
    conversation_id: uuid.UUID
    user_id: uuid.UUID




class User(BaseModel):
    id: Optional[int] = Field(alias='id')
    user_id: str = Field(alias='user_id')
    username: Optional[str] = Field(alias='username')
    created_at: Optional[datetime] = Field(alias='created_at')

class Conversation(BaseModel):
    id: Optional[int] = Field(alias='id')
    conversation_id: str = Field(alias='conversation_id')
    user_id: str = Field(alias='user_id')
    topic: Optional[str] = Field(alias='topic')
    save_chat: Optional[bool] = Field(alias='save_chat')
    language: Optional[str] = Field(alias='language')
    created_at: Optional[datetime] = Field(alias='created_at')
    modified_at: Optional[datetime] = Field(alias='modified_at')

# class Message(BaseModel):
#     id: Optional[int] = Field(alias='id')
#     conversation_id: str = Field(alias='conversation_id')
#     id_message: int = Field(alias='id_message')
#     message_text: dict = Field(alias='message_text')
#     created_at: Optional[datetime] = Field(alias='created_at')