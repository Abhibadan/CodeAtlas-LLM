from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from requestDTOs.chatDTO import ChatDTO, DocumentDTO
from middleware.authMiddleware import AuthMiddleware
from components.ragAgent import RagAgent
from dbModule.MongoDb import MongoDb
from bson import ObjectId
import json     
import asyncio

dbInstance = MongoDb()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(data: ChatDTO = Body(...)):  # Make endpoint async
    question = data.query
    pID = data.pid
    
    # Validate pID before converting to ObjectId
    if not pID or not all(c in "0123456789abcdefABCDEF" for c in pID) or len(pID) != 24:
        return StreamingResponse(
            iter([json.dumps({"error": "Invalid or missing Project ID"})]), 
            status_code=400,
            media_type="application/json"
        )
        
    try:
        project_doc = dbInstance.getCollection("projects").find_one({"_id": ObjectId(pID)})
    except Exception as e:
        return StreamingResponse(
            iter([json.dumps({"error": f"Database lookup failed - {str(e)}"})]), 
            status_code=500,
            media_type="application/json"
        )
    
    if not project_doc:
        return StreamingResponse(
            iter([json.dumps({"error": "Project not found"})]), 
            status_code=404,
            media_type="application/json"
        )
        
    agent = RagAgent(project=project_doc["title"])
    
    async def generate_stream():
        try:
            chunk_index = 0
            
            # Stream chunks from RAG agent
            for chunk in agent.getRagChain().stream(question):
                if chunk:
                    # Format as SSE with JSON payload
                    chunk_data = {
                        "id": f"chunk-{chunk_index}",
                        "object": "chat.completion.chunk",
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": chunk
                            },
                            "finish_reason": None
                        }]
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    chunk_index += 1
                    
                    # CRITICAL: Add a small async sleep to allow the event loop to flush
                    await asyncio.sleep(0.001)  # This forces the buffer to flush
            
            # Send completion signal
            final_chunk = {
                "id": f"chunk-{chunk_index}",
                "object": "chat.completion.chunk",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            print(f"Error in stream: {e}")
            # error_data = {
            #     "error": {
            #         "message": str(e),
            #         "type": "stream_error"
            #     }
            # }
            yield f"data: {json.dumps({'error': 'Something went wrong! Please try again.'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
