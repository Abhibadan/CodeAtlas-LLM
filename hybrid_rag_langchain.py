import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from neo4j import GraphDatabase
from typing import Dict, List, Any
from config import config 

# Configuration
API_KEY = config["OPENAI_API_KEY"]
BASE_URL = config["OPENAI_BASE_URL"]
CHROMA_PERSIST_DIR = config["CHROMA_PERSIST_DIR"]
NEO4J_URI = config["NEO4J_URI"]
NEO4J_USER = config["NEO4J_USER"]
NEO4J_PASSWORD = config["NEO4J_PASSWORD"]
NEO4J_DATABASE = config["NEO4J_DATABASE"]


class Neo4jRetriever:
    """Dynamic retriever for Neo4j graph data using LLM-generated Cypher queries"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j", llm=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.llm = llm
        self._schema_cache = None
    
    def close(self):
        self.driver.close()
    
    def get_schema(self) -> str:
        """Fetch the Neo4j database schema dynamically"""
        if self._schema_cache:
            return self._schema_cache
        
        with self.driver.session(database=self.database) as session:
            schema_parts = []
            
            # Get node labels and their properties
            node_info = session.run("""
                CALL db.schema.nodeTypeProperties() 
                YIELD nodeLabels, propertyName, propertyTypes
                RETURN nodeLabels, collect({property: propertyName, types: propertyTypes}) as properties
            """)
            
            schema_parts.append("=== NODE LABELS AND PROPERTIES ===")
            for record in node_info:
                labels = record["nodeLabels"]
                properties = record["properties"]
                label_str = ":".join(labels) if labels else "Unknown"
                props = [f"{p['property']} ({', '.join(p['types']) if p['types'] else 'any'})" 
                        for p in properties if p['property']]
                schema_parts.append(f"({label_str}) - Properties: {', '.join(props) if props else 'none'}")
            
            # Get relationship types and their properties
            rel_info = session.run("""
                CALL db.schema.relTypeProperties()
                YIELD relType, propertyName, propertyTypes
                RETURN relType, collect({property: propertyName, types: propertyTypes}) as properties
            """)
            
            schema_parts.append("\n=== RELATIONSHIP TYPES AND PROPERTIES ===")
            for record in rel_info:
                rel_type = record["relType"]
                properties = record["properties"]
                props = [f"{p['property']} ({', '.join(p['types']) if p['types'] else 'any'})" 
                        for p in properties if p['property']]
                schema_parts.append(f"[{rel_type}] - Properties: {', '.join(props) if props else 'none'}")
            
            # Get relationship patterns (which nodes connect to which)
            patterns = session.run("""
                CALL db.schema.visualization() YIELD nodes, relationships
                UNWIND relationships as rel
                RETURN DISTINCT 
                    [label IN labels(startNode(rel)) | label] as startLabels,
                    type(rel) as relType,
                    [label IN labels(endNode(rel)) | label] as endLabels
            """)
            
            schema_parts.append("\n=== RELATIONSHIP PATTERNS ===")
            for record in patterns:
                start = ":".join(record["startLabels"]) if record["startLabels"] else "Node"
                rel = record["relType"]
                end = ":".join(record["endLabels"]) if record["endLabels"] else "Node"
                schema_parts.append(f"({start})-[:{rel}]->({end})")
            
            self._schema_cache = "\n".join(schema_parts)
        
        return self._schema_cache
    
    def generate_cypher_query(self, question: str) -> str:
        """Use LLM to generate a Cypher query based on schema and question"""
        if not self.llm:
            return None
        
        schema = self.get_schema()
        
        prompt = f"""You are a Neo4j Cypher query expert. Generate a Cypher query to answer the user's question based on the database schema provided.
                    DATABASE SCHEMA:
                    {schema}
                    USER QUESTION: {question}
                    IMPORTANT RULES:
                    1. Only use node labels, relationship types, and properties that exist in the schema
                    2. Return meaningful data that helps answer the question
                    3. Use OPTIONAL MATCH for relationships that may not exist
                    4. Include relevant properties in the RETURN clause
                    5. Use appropriate aggregation functions like collect() for multiple relationships
                    6. Make queries case-insensitive for name searches using toLower()
                    7. Return data in a structured format with clear aliases
                    8. If the question is about referrals or connections, explore friend-of-friend relationships
                    9. ONLY output the Cypher query, no explanations

                    CYPHER QUERY:"""
        try:
            response = self.llm.invoke(prompt)
            query = response.content.strip()
            
            # Clean up the query - remove markdown code blocks if present
            if query.startswith("```"):
                lines = query.split("\n")
                query = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            # Remove any remaining markdown or explanations
            query = query.replace("```cypher", "").replace("```", "").strip()
            
            return query
        except Exception as e:
            print(f"Error generating Cypher query: {e}")
            return None
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        if not query:
            return []
        
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run(query)
                records = [record.data() for record in result]
                return records
            except Exception as e:
                print(f"Error executing Cypher query: {e}")
                print(f"Query was: {query}")
                return []
    
    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format query results into readable text"""
        if not results:
            return ""
        
        parts = ["=== KNOWLEDGE GRAPH RESULTS ==="]
        parts.append(f"Query executed: {query[:100]}..." if len(query) > 100 else f"Query executed: {query}")
        parts.append(f"Found {len(results)} result(s)\n")
        
        for i, record in enumerate(results, 1):
            parts.append(f"--- Result {i} ---")
            for key, value in record.items():
                if isinstance(value, list):
                    # Handle list of dictionaries
                    if value and isinstance(value[0], dict):
                        parts.append(f"{key}:")
                        for item in value:
                            if any(v for v in item.values() if v is not None):
                                item_str = ", ".join(f"{k}: {v}" for k, v in item.items() if v is not None)
                                parts.append(f"  - {item_str}")
                    else:
                        parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, dict):
                    parts.append(f"{key}:")
                    for k, v in value.items():
                        if v is not None:
                            parts.append(f"  {k}: {v}")
                else:
                    parts.append(f"{key}: {value}")
            parts.append("")
        
        return "\n".join(parts)
    
    def retrieve(self, question: str) -> str:
        """Main retrieval method that generates and executes dynamic Cypher queries"""
        # Generate Cypher query using LLM
        cypher_query = self.generate_cypher_query(question)
        
        if not cypher_query:
            return ""
        
        print(f"\n[Neo4j] Generated Cypher Query:\n{cypher_query}\n")
        
        # Execute the query
        results = self.execute_query(cypher_query)
        
        # Format and return results
        return self.format_results(results, cypher_query)


def format_docs(docs):
    """Format retrieved documents from ChromaDB"""
    if not docs:
        return ""
    return "\n\n=== DETAILED INFORMATION FROM DOCUMENTS ===\n" + "\n\n".join(doc.page_content for doc in docs)


def create_hybrid_context(chroma_docs: str, neo4j_context: str) -> str:
    """Combine ChromaDB and Neo4j contexts"""
    contexts = []
    
    if neo4j_context:
        contexts.append(neo4j_context)
    
    if chroma_docs:
        contexts.append(chroma_docs)
    
    return "\n\n".join(contexts) if contexts else "No relevant information found."


def main():
    # 1. Initialize Embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002", 
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    # 2. Check and Load ChromaDB
    if not os.path.exists(CHROMA_PERSIST_DIR):
        print(f"Error: {CHROMA_PERSIST_DIR} not found. Please create the ChromaDB first.")
        return
    
    vector_store = Chroma(
        persist_directory=CHROMA_PERSIST_DIR, 
        embedding_function=embeddings
    )
    
    # 3. Create ChromaDB Retriever
    chroma_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    # 4. Initialize LLM (moved up - needed for Neo4j dynamic query generation)
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    # 5. Initialize Neo4j Retriever with LLM for dynamic query generation
    neo4j_retriever = Neo4jRetriever(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        llm=llm  # Pass LLM for dynamic Cypher query generation
    )
    
    # 6. Define Hybrid RAG Prompt
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant that provides comprehensive information about people, their professional backgrounds, and relationships.
        Use the following context to answer the question. The context includes:
        1. Relationship information (friends, employment, directorships) from the knowledge graph
        2. Detailed professional information from documents

        Provide a natural, conversational answer that synthesizes both sources of information.

        Context:
        {context}"""),
        ("human", "{question}"),
    ])
    
    # 7. Create Hybrid RAG Chain
    # This chain retrieves from both ChromaDB and Neo4j, then combines the contexts
    def hybrid_retrieval(question):
        """Retrieve from both ChromaDB and Neo4j"""
        # Get documents from ChromaDB
        chroma_docs = chroma_retriever.invoke(question)
        chroma_context = format_docs(chroma_docs)
        
        # Get graph data from Neo4j
        neo4j_context = neo4j_retriever.retrieve(question)
        
        # Combine both contexts
        combined_context = create_hybrid_context(chroma_context, neo4j_context)
        
        return combined_context
    
    # Build the chain
    hybrid_rag_chain = (
        {
            "context": lambda x: hybrid_retrieval(x),
            "question": RunnablePassthrough()
        }
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    
    # 8. Test the chain with different questions
    print("="*70)
    print("HYBRID RAG SYSTEM - ChromaDB + Neo4j")
    print("="*70)
    
    questions = [
        "Who is Bob Smith? Tell me about his profession and friends details.",
        "What does Bob Smith do professionally and who does he work with?",
        "Tell me about Alice Johnson's background and connections.",
        "Give me the list who can reffer whom in which company for which skill set (employee can reffer his friend or friend of friend)"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}: {question}")
        print('='*70)
        
        try:
            print(f"\nAnswer:")
            # Stream the response chunk by chunk
            for chunk in hybrid_rag_chain.stream(question):
                print(chunk, end="", flush=True)
            print()  # New line after streaming completes
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Clean up
    neo4j_retriever.close()
    print("\n" + "="*70)
    print("Done!")


if __name__ == "__main__":
    main()