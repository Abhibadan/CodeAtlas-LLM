from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from requestDTOs.chatDTO import ChatDTO, DocumentDTO
from middleware.authMiddleware import AuthMiddleware
from components.ragAgent import RagAgent

app = FastAPI()
agent = RagAgent()

# app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat")
def chat(data: ChatDTO = Body(...)):
    question = data.query
    
    async def generate_sse():
        for chunk in agent.getRagChain().stream(question):
            # Format each chunk as SSE data
            yield f"data: {chunk}\n\n"
        # Send a done signal
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/addDocument")
def addDocument(data: DocumentDTO = Body(...)):
    from langchain_core.documents import Document
    
    # Extract document content and relatedIds from the request
    document_content = data.document
    related_ids = data.relatedIds
    
    # Create a ChromaDB-compatible document with relatedIds in metadata
    chroma_document = Document(
        page_content=document_content,
        metadata={"relatedIds": related_ids}
    )
    
    # Store the document in ChromaDB using VectorStore
    agent.getVectorStore().add_documents([chroma_document])
    
    return {
        "status": "success",
        "message": "Document added successfully",
        "relatedIds": related_ids
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
