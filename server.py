from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from requestDTOs.chatDTO import ChatDTO, DocumentDTO
from middleware.authMiddleware import AuthMiddleware
from components.ragAgent import RagAgent
from dbModule.MongoDb import MongoDb
dbInstance = MongoDb()

app = FastAPI()

# app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat")
def chat(data: ChatDTO = Body(...)):
    question = data.query
    pID = data.PID
    projects = dbInstance.getCollection("projects").find_one({"_id": pID})
    agent = RagAgent(project=projects["projectName"])
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
