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
                - metadata: Related node IDs and other metadata
            """
            try:
                result = self.vector_db.retrieve_with_metadata(query)
                return json.dumps({
                    "content": result.get("content", ""),
                    "relatedNodeIds": result.get("metadata", {}).get("relatedNodeIds", [])
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
            Query the code knowledge graph to understand relationships and dependencies.
            
            Use this tool when you need to:
            - Understand code dependencies and relationships
            - Trace execution flows between components
            - Analyze impact of changes across the codebase
            - Find connections between different code elements
            
            IMPORTANT: This tool generates and executes Cypher queries dynamically.
            For best results, first use vector_search to get relevant node IDs.
            
            Args:
                query: The question or analysis you want to perform
                documentation: Optional context from vector search (improves query accuracy)
                node_ids: Optional comma-separated node IDs from vector search (improves query accuracy)
                
            Returns:
                Formatted results from the graph database including:
                - Node properties (name, type, source code, etc.)
                - Relationships between nodes
                - Dependency chains
            """
            try:
                result = self.graph_db.retrieve_with_metadata(query)
                return result
            except Exception as e:
                return f"Graph query failed: {str(e)}"
        
        return [vector_search,get_graph_schema, graph_query]
