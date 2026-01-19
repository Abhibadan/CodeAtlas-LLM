from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import List
class VectorDb:
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
    
    def format_docs(self,docs):
        """Format retrieved documents from ChromaDB"""
        if not docs:
            return ""
        return "\n\n=== DETAILED INFORMATION FROM DOCUMENTS ===\n" + "\n\n".join(doc.page_content for doc in docs)
    
    def retrieve_raw(self, query, k=4) -> List[Document]:
        return self.client.similarity_search(query, k=k)
    
    def retrieve(self, query, k=4) -> List[Document]:
        docs = self.retrieve_raw(query, k=k)
        return self.format_docs(docs)