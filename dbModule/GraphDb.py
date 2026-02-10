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
        """Get database schema by sampling actual data - no deprecated procedures"""
        if self._schema_cache:
            return self._schema_cache
        
        with self.driver.session(database=self.database) as session:
            schema_parts = []
            
            try:
                # Get node labels and their properties by sampling
                schema_parts.append("=== NODE LABELS AND PROPERTIES ===")
                
                labels_result = session.run("CALL db.labels() YIELD label RETURN label")
                labels = [record["label"] for record in labels_result]
                
                for label in labels:
                    try:
                        # Escape label for use in Cypher
                        escaped_label = label.replace('`', '``')
                        
                        props_result = session.run(f"""
                            MATCH (n:`{escaped_label}`)
                            WITH n LIMIT 100
                            UNWIND keys(n) as key
                            WITH key, n[key] as value
                            RETURN DISTINCT key, 
                                collect(DISTINCT type(value))[0..3] as types
                            ORDER BY key
                        """)
                        
                        props = []
                        for record in props_result:
                            prop_name = record["key"]
                            types = record.get("types", [])
                            type_str = ', '.join(str(t) for t in types) if types else 'any'
                            props.append(f"{prop_name} ({type_str})")
                        
                        schema_parts.append(f"({label}) - Properties: {', '.join(props) if props else 'none'}")
                    
                    except Exception as e:
                        schema_parts.append(f"({label}) - Error fetching properties: {str(e)}")
                
                # Get relationship types and their properties
                schema_parts.append("\n=== RELATIONSHIP TYPES AND PROPERTIES ===")
                
                rel_types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
                rel_types = [record["relationshipType"] for record in rel_types_result]
                
                for rel_type in rel_types:
                    try:
                        # Escape relationship type for use in Cypher
                        escaped_rel = rel_type.replace('`', '``')
                        
                        props_result = session.run(f"""
                            MATCH ()-[r:`{escaped_rel}`]->()
                            WITH r LIMIT 100
                            UNWIND keys(r) as key
                            WITH key, r[key] as value
                            RETURN DISTINCT key,
                                collect(DISTINCT type(value))[0..3] as types
                            ORDER BY key
                        """)
                        
                        props = []
                        for record in props_result:
                            prop_name = record["key"]
                            types = record.get("types", [])
                            type_str = ', '.join(str(t) for t in types) if types else 'any'
                            props.append(f"{prop_name} ({type_str})")
                        
                        schema_parts.append(f"[{rel_type}] - Properties: {', '.join(props) if props else 'none'}")
                    
                    except Exception as e:
                        schema_parts.append(f"[{rel_type}] - Error fetching properties: {str(e)}")
                
                # Get relationship patterns
                schema_parts.append("\n=== RELATIONSHIP PATTERNS ===")
                
                patterns = session.run("""
                    MATCH (start)-[rel]->(end)
                    WITH DISTINCT labels(start) as startLabels, 
                                type(rel) as relType, 
                                labels(end) as endLabels
                    RETURN startLabels, relType, endLabels
                    LIMIT 1000
                """)
                
                seen_patterns = set()
                for record in patterns:
                    start_labels = record["startLabels"]
                    rel = record["relType"]
                    end_labels = record["endLabels"]
                    
                    start = ":".join(start_labels) if start_labels else "Node"
                    end = ":".join(end_labels) if end_labels else "Node"
                    pattern = f"({start})-[:{rel}]->({end})"
                    
                    if pattern not in seen_patterns:
                        schema_parts.append(pattern)
                        seen_patterns.add(pattern)
            
            except Exception as e:
                schema_parts.append(f"Error fetching schema: {str(e)}")
                # Fallback to minimal schema
                schema_parts.append("\n=== BASIC SCHEMA INFO ===")
                try:
                    # At least get labels and relationship types
                    labels_result = session.run("CALL db.labels() YIELD label RETURN label")
                    labels = [record["label"] for record in labels_result]
                    schema_parts.append(f"Node Labels: {', '.join(labels)}")
                    
                    rel_types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
                    rel_types = [record["relationshipType"] for record in rel_types_result]
                    schema_parts.append(f"Relationship Types: {', '.join(rel_types)}")
                except Exception as inner_e:
                    schema_parts.append(f"Could not fetch basic schema: {str(inner_e)}")
            
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

                RELEVANT SEARCH IDS (as comma-separated string): "{node_ids_str}"

                RELATED DOCUMENTATION: {documentation}

                QUERY OBJECTIVE:
                Construct a Cypher query that fetches relevant nodes and their context using semantic matching on node properties rather than internal IDs.

                MATCHING STRATEGY:
                1. Parse the search terms from RELEVANT SEARCH IDS,RELATED DOCUMENTATION and USER QUESTION to derive regex patterns
                2. Match nodes using `eid`, `parentId`, or regex patterns on searchable fields
                3. Use OR conditions to cast a wide net for relevant nodes
                4. Fetch relationships and context around matched nodes

                SEARCHABLE FIELDS FOR REGEX MATCHING:
                - eid
                - parentId
                - name
                - sourceCode
                - parameters
                - type
                - subType
                - filePath
                - kind


                CRITICAL SYNTAX RULES:
                1. Use property-based matching, NOT id() function
                2. Derive regex patterns from the question context and search terms
                3. Use case-insensitive regex: =~ '(?i).*pattern.*'
                4. Combine multiple match conditions with OR
                5. NEVER NEST AGGREGATE FUNCTIONS
                6. ALL variables used in collect() MUST be defined in the current MATCH clause
                7. Use OPTIONAL MATCH for relationships to avoid losing nodes without connections

                QUERY STRUCTURE TEMPLATE:
                ```
                // Step 1: Parse search terms and create matching conditions
                WITH "{node_ids_str}" AS searchTerms
                WITH split(searchTerms, ",") AS terms

                // Step 2: Match nodes using eid, parentId, or regex patterns
                MATCH (n)
                WHERE n.eid IN terms
                OR n.parentId IN terms
                OR ANY(term IN terms WHERE 
                    n.name =~ ('(?i).*' + term + '.*')
                    OR n.sourceCode =~ ('(?i).*' + term + '.*')
                    OR n.parameters =~ ('(?i).*' + term + '.*')
                    OR n.type =~ ('(?i).*' + term + '.*')
                    OR n.subType =~ ('(?i).*' + term + '.*')
                    OR n.filePath =~ ('(?i).*' + term + '.*')
                    OR n.kind =~ ('(?i).*' + term + '.*')
                )

                // Step 3: Fetch relationships and build context
                ...
                ```

                SAFE PATTERNS FOR RELATIONSHIPS:

                PATTERN 1 - Direct relationships with regex matching:
                ```
                WITH "{node_ids_str}" AS searchTerms
                WITH split(searchTerms, ",") AS terms
                MATCH (n)
                WHERE n.eid IN terms
                OR n.parentId IN terms
                OR ANY(term IN terms WHERE 
                    n.name =~ ('(?i).*' + term + '.*')
                    OR n.type =~ ('(?i).*' + term + '.*')
                    OR n.filePath =~ ('(?i).*' + term + '.*')
                )
                OPTIONAL MATCH (n)-[r1]->(m1)
                WITH n, collect(DISTINCT {{relationship: type(r1), target: m1}}) AS outgoing
                OPTIONAL MATCH (n)<-[r2]-(m2)
                WITH n, outgoing, collect(DISTINCT {{relationship: type(r2), source: m2}}) AS incoming
                RETURN n, outgoing, incoming
                ```

                PATTERN 2 - Multi-hop with pattern comprehensions:
                ```
                WITH "{node_ids_str}" AS searchTerms
                WITH split(searchTerms, ",") AS terms
                MATCH (n)
                WHERE n.eid IN terms
                OR ANY(term IN terms WHERE 
                    n.name =~ ('(?i).*' + term + '.*')
                    OR n.sourceCode =~ ('(?i).*' + term + '.*')
                )
                RETURN n,
                    [(n)-[r]->(m) | {{rel_type: type(r), node: m}}] AS direct_out,
                    [(n)<-[r]-(m) | {{rel_type: type(r), node: m}}] AS direct_in,
                    [(n)-[*1..2]->(m) WHERE m.type IS NOT NULL | m] AS transitive_out
                LIMIT 100
                ```

                PATTERN 3 - Context-aware traversal:
                ```
                WITH "{node_ids_str}" AS searchTerms
                WITH split(searchTerms, ",") AS terms
                MATCH (n)
                WHERE ANY(term IN terms WHERE 
                    n.name =~ ('(?i).*' + term + '.*')
                    OR n.eid = term
                    OR n.parentId = term
                )
                CALL {{
                WITH n
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN collect({{rel: type(r), props: properties(r), target: properties(m)}}) AS rels
                }}
                RETURN properties(n) AS node, rels
                LIMIT 50
                ```

                REGEX PATTERN DERIVATION GUIDELINES:
                1. Extract key entities from the question (function names, class names, file names)
                2. Convert camelCase/snake_case terms into flexible patterns
                3. For code analysis, prioritize: function names, class names, method signatures
                4. For dependency queries, focus on: import paths, module names, file paths
                5. Use partial matching with '.*' prefix/suffix for flexibility

                EXAMPLES OF PATTERN DERIVATION:

                Question: "Find all functions that call getUserData"
                → Search for: name =~ '(?i).*getUserData.*' OR sourceCode =~ '(?i).*getUserData.*'

                Question: "Show dependencies of auth module"
                → Search for: filePath =~ '(?i).*auth.*' OR name =~ '(?i).*auth.*'

                Question: "Find classes implementing IUserService"
                → Search for: type =~ '(?i).*class.*' AND sourceCode =~ '(?i).*IUserService.*'

                OPTIMIZATION RULES:
                1. Always add LIMIT clause (50-100) to prevent massive result sets
                2. Use DISTINCT in collections to avoid duplicates
                3. Filter by node labels if schema provides them
                4. Use property existence checks: WHERE n.name IS NOT NULL
                5. Consider using indexes if available on eid, name, filePath

                COMMON MISTAKES TO AVOID:
                ❌ Using id(n) instead of n.eid
                ❌ Forgetting case-insensitive flag (?i) in regex
                ❌ Not escaping special regex characters in search terms
                ❌ Collecting variables that are out of scope after WITH
                ✅ Use property-based matching with flexible regex patterns
                ✅ Combine multiple search strategies with OR
                ✅ Collect relationship data before WITH statements

                OUTPUT FORMAT:
                Generate ONLY the Cypher query without any explanations, comments, or markdown formatting.
                The query must be production-ready and handle edge cases gracefully.
                Ensure the query uses semantic matching based on the question and documentation context.

                CYPHER QUERY:"""
        
        prompt = prompt.replace("{schema}", schema)
        prompt = prompt.replace("{question}", question)
        prompt = prompt.replace("{node_ids_str}", node_ids_str)
        prompt = prompt.replace("{documentation}", documentation)

        try:
            response = llm.invoke(prompt)
            query = response.content.strip()
            print("Generated Cypher query:", query)
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

            
    
    