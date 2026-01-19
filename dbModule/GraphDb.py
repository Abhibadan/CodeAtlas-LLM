from neo4j import GraphDatabase
from typing import List, Dict, Any, Generator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class GraphDb:
    __instance = None
    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self,uri,user,password,database):
        if self._initialized:
            return
        self._initialized = True
        self.driver = GraphDatabase.driver(uri,auth=(user,password))
        self.database = database
        self._schema_cache = None

    def close(self):
        self.driver.close()
    
    def get_schema(self) -> str:
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
    
    def generate_cypher_query(self, llm, question: str,details: str) -> str:
        """Use LLM to generate a Cypher query based on schema and question"""
        
        schema = self.get_schema()
        prompt = f"""You are a Neo4j Cypher query expert. Generate a Cypher query to answer the user's question based on the database schema provided.
                    DATABASE SCHEMA:
                    {schema}
                    USER QUESTION: {question}
                    USER DETAILS: {details}
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
            response = llm.invoke(prompt)
            query = response.content.strip()
            # Clean up the query - remove markdown code blocks if present
            if query.startswith("```"):
                lines = query.split("\n")
                query = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            # Remove any remaining markdown or explanations
            query = query.replace("```cypher", "").replace("```", "").strip()
            
            return query
        except Exception as e:
            raise Exception(f"Error generating Cypher query: {e}")
    
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
                raise Exception(f"Error executing Cypher query: {e}")
    
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
    
    def retrieve(self, llm, question: str,details: str) -> str:
        """Main retrieval method that generates and executes dynamic Cypher queries"""
        try:
            # Generate Cypher query using LLM
            cypher_query = self.generate_cypher_query(llm,question,details)
            if not cypher_query:
                return ""
            
            
            # Execute the query
            results = self.execute_query(cypher_query)

            
            # Format and return results
            return self.format_results(results, cypher_query)
        except Exception as e:
            raise Exception(e.__str__())

            
    
    