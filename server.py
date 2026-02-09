from fastapi import FastAPI, Query, Body, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from requestDTOs.chatDTO import ChatDTO
from middleware.authMiddleware import AuthMiddleware
from components import RagAgent
from dbModule import init_db, Project, Conversation, ConversationTypeEnum, ConversationRoleEnum
from bson import ObjectId
import json     
import asyncio

# Initialize MongoDB connection using MongoEngine
from config import mongo_config
init_db(database_name=mongo_config["db"], host=mongo_config["uri"])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.5.80:3000", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.add_middleware(AuthMiddleware)

@app.post("/api/conversation")
async def conversation(request: Request, data: ChatDTO = Body(...)):  # Make endpoint async
    question = data.query
    pID = data.pid
    # Validate pID before converting to ObjectId
    if not pID or not all(c in "0123456789abcdefABCDEF" for c in pID) or len(pID) != 24:
        return StreamingResponse(
            iter([json.dumps({
                "id": "chunk-0",
                "object": "chat.error.chunk",
                "delta": {
                    "content": "Invalid or missing Project ID"
                },
                "finish_reason": "error"
            })]), 
            status_code=400,
            media_type="application/json"
        )
        
    try:
        # Use MongoEngine to query project
        project = Project.find_by_id(id=ObjectId(pID))
        
        # Check if project exists before processing
        if not project:
            return StreamingResponse(
                iter([json.dumps({
                    "id": "chunk-0",
                    "index": 0,
                    "object": "chat.error.chunk",
                    "delta": {
                        "content": "Project not found"
                    },
                    "finish_reason": "error"
                })]), 
                status_code=404,
                media_type="application/json"
            )
        
        project_uuid = project.uuid

        conversation = Conversation(
            chat_id=ObjectId(data.cid),
            user_id=request.state.user.id,
            content=question,
            type=ConversationTypeEnum.TEXT.value,
            role=ConversationRoleEnum.USER.value
        )
        conversation.save() 
    except Exception as e:
        return StreamingResponse(
            iter([json.dumps({
                "id": "chunk-0",
                "index": 0,
                "object": "chat.error.chunk",
                "delta": {
                    "content": f"Database error"
                },
                "finish_reason": "error"
            })]), 
            status_code=500,
            media_type="application/json"
        )
    
    # Use the extracted uuid
    agent = RagAgent({
        "project": project_uuid,
        "chatId": data.cid,
        "convId": data.convId   
    })
    
    async def generate_stream():
        try:
            chunk_index = 0
            full_response = ""
            
            # Stream chunks from RAG agent
            for chunk in agent.getRagChain().stream(question):
                if chunk:
                    full_response += chunk
                    # Format as SSE with JSON payload
                    chunk_data = {
                        "id": f"chunk-{chunk_index}",
                        "index": chunk_index,
                        "object": "chat.data.chunk",
                        "delta": {
                            "content": chunk
                        },
                        "finish_reason": None
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    chunk_index += 1
                    
                    # CRITICAL: Add a small async sleep to allow the event loop to flush
                    await asyncio.sleep(0.001)  # This forces the buffer to flush
            
            # Send completion signal
            final_chunk = {
                "id": f"chunk-{chunk_index}",
                "index": chunk_index,
                "object": "chat.completion.chunk",
                "delta": {
                    "content": ""
                },
                "finish_reason": "stop"
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield f"data: [DONE]\n\n"

            # store in db
            conversation = Conversation(
                chat_id=ObjectId(data.cid),
                user_id=request.state.user.id,
                content=full_response,
                type=ConversationTypeEnum.TEXT.value,
                role=ConversationRoleEnum.ASSISTANT.value
            )
            conversation.save()

        except Exception as e:
            print(f"Error in stream: {e}")
            error_chunk = {
                "id": f"chunk-0",
                "index": 0,
                "object": "chat.error.chunk",
                "delta": {
                    "content": "Something went wrong! Please try again."
                },
                "finish_reason": "error"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
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
