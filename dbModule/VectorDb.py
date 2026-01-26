import chromadb
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import List

class VectorDb:
    def __init__(self, host, port, collection, embedding_model, api_key):
        # Use the same embedding function
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )
        
        self.collection_name = collection
        
        # Create HTTP client for remote ChromaDB server
        chroma_client = chromadb.HttpClient(
            host=host,
            port=int(port)
        )
        
        # Use Langchain Chroma with the HTTP client
        self.client = Chroma(
            client=chroma_client,
            collection_name=collection,
            embedding_function=embeddings
        )
    
    def add_documents(self, documents):
        self.client.add(documents)
    
    def clear_collection(self):
        self.client.reset_collection()

    
    def addDocument(self, content: str, metadata: dict = None):
        """
        Add a document to the vector store with metadata.
        
        Args:
            content: The cleaned content of the document
            metadata: Dictionary containing filePath, fileName, relatedNodeIds, matchType, etc.
        """
        if metadata is None:
            metadata = {}
        
        # Skip empty content to avoid embedding errors
        if not content or not content.strip():
            print(f"Warning: Skipping empty document for {metadata.get('fileName', 'unknown')}")
            return
        
        # Create a single document with the content and metadata
        document = Document(page_content=content, metadata=metadata)
        
        # Add document to the vector store
        self.client.add_documents([document])

    
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