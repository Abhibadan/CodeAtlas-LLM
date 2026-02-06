from neo4j import GraphDatabase
from typing import List, Dict, Any, Generator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class GraphDb:
    def __init__(self,uri,user,password,database):
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
    
    def generate_cypher_query(self, llm, question: str, documentation: str, node_ids: str) -> str:
        """Use LLM to generate a Cypher query based on schema and question"""
        
        # Pass node_ids directly as a cleaned string
        if isinstance(node_ids, str):
            # Remove empty strings and extra commas
            node_ids_str = ",".join([nid.strip() for nid in node_ids.split(',') if nid.strip()])
        else:
            node_ids_str = str(node_ids)
        
        schema = self.get_schema()
        prompt = """You are a Neo4j Cypher query expert specializing in code dependency graph traversal. Generate a SYNTACTICALLY CORRECT Cypher query to fetch relevant code components and their relationships for code analysis.

        DATABASE SCHEMA:
        {schema}

        USER QUESTION: {question}

        RELEVANT NODE IDs (as comma-separated string): "{node_ids_str}"

        RELATED DOCUMENTATION: {documentation}

        QUERY OBJECTIVE:
        Construct a Cypher query that fetches relevant nodes and their context starting from the provided node IDs.

        CRITICAL SYNTAX RULES:
        1. START with: WITH split("{node_ids_str}", ",") AS startNodeIds
        2. Then use: MATCH (n) WHERE id(n) IN startNodeIds
        3. NEVER use WHERE inside list comprehensions.
        4. ZERO TOLERANCE: NEVER NEST AGGREGATE FUNCTIONS. Do NOT put collect() inside another collect(). 
           BAD: collect({ a: collect(b) }) -> THIS WILL FAIL.
        5. FOR MULTI-LEVEL RESULTS: Use multiple WITH clauses to aggregate sequentially, OR return flat paths.
        6. Return data in a structured format with clear aliases.

        SAFE MULTI-HOP PATTERN:
        WITH split("{node_ids_str}", ",") AS startNodeIds
        MATCH (n) WHERE id(n) IN startNodeIds
        OPTIONAL MATCH (n)-[r1]->(n1)
        WITH n, collect(DISTINCT {rel: r1, node: n1}) AS level1
        OPTIONAL MATCH (n)-[]->(n1)-[r2]->(n2)
        WITH n, level1, collect(DISTINCT {rel: r2, node: n2}) AS level2
        RETURN n, level1, level2

        OUTPUT FORMAT:
        Generate ONLY the Cypher query without any explanations, comments, or markdown formatting.
        Ensure the query is syntactically correct and will execute without errors.

        CYPHER QUERY:"""
        
        prompt = prompt.replace("{schema}", schema)
        prompt = prompt.replace("{question}", question)
        prompt = prompt.replace("{node_ids_str}", node_ids_str)
        prompt = prompt.replace("{documentation}", documentation)

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
    
    def retrieve(self, llm, question: str, details: str, relatedNodeIds: List[str]) -> str:
        """Main retrieval method that generates and executes dynamic Cypher queries"""
        try:
            # Generate Cypher query using LLM
            cypher_query = self.generate_cypher_query(llm, question, details, relatedNodeIds)
            if not cypher_query:
                return ""
            
            # Debug: Print the generated query
            # 
            #  "="*80)
            # print("GENERATED CYPHER QUERY:")
            # print(cypher_query)
            # print("="*80)
            
            # Execute the query
            results = self.execute_query(cypher_query)

            
            # Format and return results
            return self.format_results(results, cypher_query)
        except Exception as e:
            print(f"Error in retrieve method: {e}")
            raise Exception(e.__str__())

            
    
    