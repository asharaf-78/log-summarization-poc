from pydantic import BaseModel
from typing_extensions import List,Annotated

class ChatModel(BaseModel):
    query: str


class ReponseModel(BaseModel):
    response: str 
    references : List[str]

class QueryOutput(BaseModel):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]
