from pydantic import BaseModel
from typing import Optional

class ChatDTO(BaseModel):
    query: str
    pid: str
    cid: str
    convId: Optional[str] = None
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Hello World",
                "pid": "675c2b3b3b3b3b3b3b3b3b3b",
                "cid": "675c2b3b3b3b3b3b3b3b3b3b",
                "convId": "675c2b3b3b3b3b3b3b3b3b3b"
            }
        }
