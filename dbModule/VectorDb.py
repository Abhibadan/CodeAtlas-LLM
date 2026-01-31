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
        print(self.client)
    
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

    def retrieve_raw(self, query, k=4) -> List[Document]:
        return self.client.similarity_search(query, k=k)
    
    def __format_docs(self,docs):
        """Format retrieved documents from ChromaDB"""
        if not docs:
            return ""
        return "\n\n=== DETAILED INFORMATION FROM DOCUMENTS ===\n" + "\n\n".join(doc.page_content for doc in docs)
    
    def retrieve_document_only(self, query, k=4) -> List[Document]:
        docs = self.retrieve_raw(query, k=k)
        return self.__format_docs(docs)

    def __format_metadata_docs(self,docs):
        """Format retrieved documents from ChromaDB"""
        if not docs:
            return {
                "content": "",
                "metadata": {
                    "fileName": "",
                    "filePath": "",
                    "relatedNodeIds": "",
                    "matchType": "",
                    "types": ""
                }
            }
        formated_docs = {
            "content": [],
            "metadata": {
                "fileName": [],
                "filePath": [],
                "relatedNodeIds": [],
                "matchType": [],
                "projectId": [],
                "projectName": [],
                "scanVersion": [],
                "types": []
            }
        }
        index = 0
        for doc in docs:
            content = f"""
            === DOCUMENT {index+1} ===

            {doc.page_content}

            File Path: {doc.metadata.get("filePath", "unknown")}
            File Name: {doc.metadata.get("fileName", "unknown")}
            Related Node IDs: {doc.metadata.get("relatedNodeIds", "unknown")}
            Match Type: {doc.metadata.get("matchType", "unmatched")}
            Project ID: {doc.metadata.get("projectId", "unknown")}
            Project Name: {doc.metadata.get("projectName", "unknown")}
            Scan Version: {doc.metadata.get("scanVersion", "unknown")}
            Type: {doc.metadata.get("type", "unknown")}
            
            """
            formated_docs["content"].append(content)
            formated_docs["metadata"]["fileName"].append(str(doc.metadata.get("fileName", "unknown")))
            formated_docs["metadata"]["filePath"].append(str(doc.metadata.get("filePath", "unknown")))
            # relatedNodeIds is already a string (comma-separated or JSON), just use it directly
            related_ids = doc.metadata.get("relatedNodeIds", "")
            if related_ids:
                formated_docs["metadata"]["relatedNodeIds"].append(str(related_ids))
            formated_docs["metadata"]["matchType"].append(str(doc.metadata.get("matchType", "unmatched")))
            formated_docs["metadata"]["types"].append(str(doc.metadata.get("type", "unknown")))
            index += 1
        return {
            "content": "\n\n=== DETAILED INFORMATION FROM DOCUMENTS ===\n" + "\n\n".join(formated_docs["content"]),
            "metadata":{
                "fileName":",".join(formated_docs["metadata"]["fileName"]),
                "filePath":",".join(formated_docs["metadata"]["filePath"]),
                "relatedNodeIds":",".join(formated_docs["metadata"]["relatedNodeIds"]) if formated_docs["metadata"]["relatedNodeIds"] else "",
                "matchType":",".join(formated_docs["metadata"]["matchType"]),
                "types":",".join(formated_docs["metadata"]["types"]),
            }
        }
    
    def retrieve_with_metadata(self, query, k=4) -> List[Document]:
        docs = self.retrieve_raw(query, k=k)
        return self.__format_metadata_docs(docs)