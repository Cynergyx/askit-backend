from pydantic import BaseModel, ConfigDict
from typing import Literal, Dict


# Accepts user question
class ChatHistory(BaseModel):
    role: Literal["user", "assistant"]
    content: Dict | str

    model_config = ConfigDict(extra="forbid")