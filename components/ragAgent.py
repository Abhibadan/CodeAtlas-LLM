from dbModule.VectorDb import VectorDb
from dbModule.GraphDb import GraphDb
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import config
from typing import List, Dict, Any
class RagAgent:
    __rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant that provides comprehensive information about people, their professional backgrounds, and relationships.
        Use the following context to answer the question. The context includes:
        1. Relationship information (friends, employment, directorships) from the knowledge graph
        2. Detailed professional information from documents

        Provide a natural, conversational answer that synthesizes both sources of information.

        Context:
        {context}"""),
        ("human", "{question}"),
    ])

    def __init__(self,project):
        self.__vectorStore = VectorDb(config["CHROMA_HOST"],config["CHROMA_PORT"],project,config["EMBEDDING_MODEL"],config["GOOGLE_API_KEY"])
        self.__graphStore = GraphDb(config["NEO4J_URI"],config["NEO4J_USER"],config["NEO4J_PASSWORD"],project)
        self.__llm = ChatGoogleGenerativeAI(
            model=config["CHAT_MODEL"],
            google_api_key=config["GOOGLE_API_KEY"]
        )

        self.__hybrid_rag_chain = (
        {
            "context": lambda x: self.__hybrid_retrieval(x),
            "question": RunnablePassthrough()
        }
        | self.__rag_prompt
        | self.__llm
        | StrOutputParser()
    )
    
    def __create_hybrid_context(self, chroma_docs: str, neo4j_context: str) -> str:
        """Combine ChromaDB and Neo4j contexts"""
        contexts = []
        if neo4j_context:
            contexts.append(neo4j_context)
        
        if chroma_docs:
            contexts.append(chroma_docs)
        
        return "\n\n".join(contexts) if contexts else "No relevant information found."

    def __hybrid_retrieval(self, question: str):
        vectorData = self.__vectorStore.retrieve(question)
        cypherQuery = self.__graphStore.retrieve(self.__llm, question, vectorData)
        return self.__create_hybrid_context(vectorData, cypherQuery)
    
    def getRagChain(self):
        return self.__hybrid_rag_chain
    
    def getVectorStore(self):
        return self.__vectorStore
        