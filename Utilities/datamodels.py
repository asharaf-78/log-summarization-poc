from pydantic import BaseModel
from typing_extensions import List,Annotated

class ChatModel(BaseModel):
    query: str
    platform_type: str


class ReponseModel(BaseModel):
    response: str 
    references : List[str]

class QueryOutput(BaseModel):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]
    references: List[str]
