from pydantic import BaseModel

class ChatDTO(BaseModel):
    query: str

    class Config:
        schema_extra = {
            "example": {
                "query": "Hello World"
            }
        }
