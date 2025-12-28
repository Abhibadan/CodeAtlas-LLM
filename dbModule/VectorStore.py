from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import List
class VectorStore:
    __instance = None

    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self,host,port,collection,embedding_model,api_key):
        if self._initialized:
            return
        self._initialized = True
        
        # Use the same embedding function
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )
        
        self.client = Chroma(
            host=host,
            port=port,
            collection_name=collection,
            embedding_function=embeddings
        )
    
    def add_documents(self, documents):
        self.client.add(documents)
    
    def retrieve(self, query, k=4) -> List[Document]:
        return self.client.similarity_search(query, k=k)