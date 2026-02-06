from pydantic import BaseModel

class ChatDTO(BaseModel):
    query: str
    pid: str
    cid: str
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Hello World",
                "pid": "675c2b3b3b3b3b3b3b3b3b3b",
                "cid": "675c2b3b3b3b3b3b3b3b3b3b"
            }
        }
