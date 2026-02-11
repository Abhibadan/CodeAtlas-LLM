"""
Agent Tools Module

This module defines LangChain tools for the RAG agent to dynamically query
vector and graph databases.
"""

from langchain.tools import tool
from typing import Dict, Any
import json


class AgentTools:
    """Container for agent tools with access to database instances"""
    
    def __init__(self, vector_db, graph_db, llm):
        """
        Initialize agent tools with database instances
        
        Args:
            vector_db: VectorDb instance for semantic search
            graph_db: GraphDb instance for graph queries
            llm: Language model for generating Cypher queries
        """
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.llm = llm
    
    def get_tools(self):
        """Return list of tools for the agent"""
        
        @tool
        def vector_search(query: str) -> str:
            """
            Search for relevant code documentation and metadata using semantic search.
            
            Use this tool when you need to:
            - Find documentation about code components
            - Discover relevant node IDs for graph queries
            - Get general information about the codebase
            
            Args:
                query: The search query describing what you're looking for
                
            Returns:
                A JSON string containing:
                - content: Relevant documentation text
                - metadata: 
                    eids: List of node IDs related to the query
                    fileName: Name of the files containing the documentation
                    filePath: Path of the files containing the documentation
                    matchType : Type of match (e.g., "module", "file", "unmatched")
                    types : Type of the documentation (e.g., "class", "function", "variable")
            """
            try:
                result = self.vector_db.retrieve_with_metadata(query)
                return json.dumps({
                    "content": result.get("content", ""),
                    "eids": result.get("metadata", {}).get("relatedNodeIds", [])
                }, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Vector search failed: {str(e)}"})
        
        @tool
        def get_graph_schema() -> str:
            """
            Get the schema of the code knowledge graph.
            
            Returns:
                A JSON string containing:
                - labels: List of node labels
                - relationships: List of relationship types
            """
            try:
                result = self.graph_db.get_schema()
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Graph schema retrieval failed: {str(e)}"})
        
        @tool
        def graph_query(cypher_query: str) -> str:
            """
            Execute a Cypher query on the code knowledge graph.
            
            ⚠️ CRITICAL: This tool requires a COMPLETE, VALID Neo4j Cypher query.
            It does NOT accept natural language - you must construct the Cypher yourself.
            
            Use this tool when you need to:
            - Understand code dependencies and relationships
            - Trace execution flows between components
            - Analyze impact of changes across the codebase
            - Find connections between different code elements
            
            WORKFLOW:
            1. Call vector_search() to get relevant node IDs
            2. Call get_graph_schema() to understand the graph structure
            3. Construct a valid Cypher query using the node IDs and schema
            4. Pass the Cypher query to this tool
            
            Args:
                cypher_query: A complete, valid Neo4j Cypher query string
                Example: "MATCH (n) WHERE n.eid IN ['met-123'] RETURN n LIMIT 10"
                
            Returns:
                JSON string containing query results with:
                - Node properties (name, type, sourceCode, filePath, etc.)
                - Relationships between nodes
                - Dependency chains
                
            Example Cypher patterns:
            - Find node by ID: "MATCH (n) WHERE n.eid = 'met-abc123' RETURN n"
            - Find callers: "MATCH (caller)-[:CALLS]->(target) WHERE target.eid = 'met-123' RETURN caller"
            - Find by name: "MATCH (n) WHERE n.name =~ '(?i).*saveUser.*' RETURN n LIMIT 10"
            """
            try:
                print("Cypher Query: ",cypher_query)
                result = self.graph_db.retrieve_with_metadata(cypher_query)
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": f"Graph query failed: {str(e)}"})
        
        return [vector_search,get_graph_schema, graph_query]
