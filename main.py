from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from dbModule.VectorStore import VectorStore
from dbModule.GraphStore import GraphStore
from requestDTOs.chatDTO import ChatDTO
from middleware.authMiddleware import AuthMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from config import config

app = FastAPI()
vectorStore = VectorStore(config["CHROMA_HOST"],config["CHROMA_PORT"],config["CHROMA_COLLECTION"],config["EMBEDDING_MODEL"],config["GOOGLE_API_KEY"])
graphStore = GraphStore(config["NEO4J_URI"],config["NEO4J_USER"],config["NEO4J_PASSWORD"],config["NEO4J_DATABASE"])

# app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat")
def chat(data: ChatDTO = Body(...)):
    question = data.query
    vectorData = vectorStore.retrieve(question)
    llm = ChatGoogleGenerativeAI(
        model=config["CHAT_MODEL"],
        google_api_key=config["GOOGLE_API_KEY"]
    )
    cypherQuery = graphStore.retrieve(llm,question)
    # graphStore.execute_query(cypherQuery)
    return {"query": question,"vectorData":vectorData,"cypherQuery":cypherQuery}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
