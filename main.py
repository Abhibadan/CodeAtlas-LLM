from fastapi import FastAPI,Query,Body
from dbModule.VectorStore import VectorStore
from requestDTOs.chatDTO import ChatDTO
from middleware.authMiddleware import AuthMiddleware
from config import config

app = FastAPI()
vectorStore = VectorStore(config["CHROMA_HOST"],config["CHROMA_PORT"],config["CHROMA_COLLECTION"],config["EMBEDDING_MODEL"],config["GOOGLE_API_KEY"])

# app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat")
def chat(data: ChatDTO = Body(...)):
    vectorData = vectorStore.retrieve(data.query)
    return {"query": data.query,"vectorData":vectorData}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
