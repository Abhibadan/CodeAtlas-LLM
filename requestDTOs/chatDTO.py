from pydantic import BaseModel

class ChatDTO(BaseModel):
    query: str
    pid: str
    class Config:
        schema_extra = {
            "example": {
                "query": "Hello World"
            }
        }

class DocumentDTO(BaseModel):
    document: str
    relatedIds: list[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "document": "Hello World",
                "relatedIds": ["id1", "id2", "id3"]
            }
        }