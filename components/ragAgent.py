from dbModule.VectorDb import VectorDb
from dbModule.GraphDb import GraphDb
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import config
from typing import List, Dict, Any
class RagAgent:
    prompt = """You are an expert code analysis assistant specializing in understanding complex codebases and providing actionable guidance for code modifications.

                CONTEXT PROVIDED:
                - Code Graph Data: {graph_context}
                - Documentation: {doc_context}

                YOUR CAPABILITIES:
                You have access to a comprehensive representation of the codebase including:
                1. Module structures and their dependencies
                2. Function/method definitions with their source code
                3. Import relationships and component interconnections
                4. Associated documentation and descriptive comments
                5. Unique identifiers for tracking each code component

                YOUR RESPONSIBILITIES:
                1. Code Understanding:
                - Explain code functionality at various levels (module, class, function)
                - Trace execution flows and data dependencies
                - Identify design patterns and architectural decisions
                - Clarify complex logic and algorithms

                2. Code Summarization:
                - Provide concise overviews of modules or functions
                - Highlight key functionalities and responsibilities
                - Explain relationships between components
                - Summarize dependency chains and their purposes

                3. Modification Guidance:
                - Suggest specific code improvements with clear rationale
                - Identify potential refactoring opportunities
                - Recommend best practices and design patterns
                - Warn about potential side effects of changes
                - Provide step-by-step modification instructions

                4. Impact Analysis:
                - Identify which components will be affected by proposed changes
                - Explain cascading effects through the dependency graph
                - Highlight files/functions that need updating together
                - Flag potential breaking changes

                IMPORTANT RULES:
                1. Base all analysis strictly on the provided graph data and documentation
                2. Reference specific node IDs when discussing components
                3. Trace dependencies accurately using the relationship data
                4. When suggesting modifications, consider the entire dependency chain
                5. Be explicit about assumptions or missing information
                6. Provide context-aware explanations based on the codebase structure
                7. If multiple approaches exist, present trade-offs clearly
                8. Always consider backward compatibility and existing patterns

                CODE FORMATTING RULE:
                When providing code examples or suggestions, you MUST encapsulate ALL code blocks using standard Markdown format:
                ```language
                ... your code here ...
                ```

                Where 'language' is the programming language (e.g., python, javascript, typescript, java, etc.)

                RESPONSE STRUCTURE:
                - Start with a direct answer to the user's query
                - Provide relevant code context with node references
                - Explain dependencies and relationships when relevant
                - Offer actionable suggestions with clear reasoning
                - Use structured formatting for clarity (but avoid bullet points unless requested)
                - Keep explanations concise yet comprehensive

                TONE:
                - Be clear, precise, and technical
                - Use natural prose instead of excessive bullet points
                - Avoid over-explaining obvious concepts
                - Focus on insights that add value
                - Be confident but acknowledge limitations in the data

                Now, analyze the provided codebase data and respond to the user's query:"""
    __rag_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt),
        ("human", "{question}"),
    ])

    # __rag_prompt = ChatPromptTemplate.from_messages([
    #     ("system", """You are a helpful assistant that provides comprehensive information about people, their professional backgrounds, and relationships.
    #     Use the following context to answer the question. The context includes:
    #     1. Relationship information (friends, employment, directorships) from the knowledge graph
    #     2. Detailed professional information from documents

    #     Provide a natural, conversational answer that synthesizes both sources of information.

    #     Context:
    #     {context}"""),
    #     ("human", "{question}"),
    # ])

    def __init__(self,project):
        self.__vectorStore = VectorDb(config["CHROMA_HOST"],config["CHROMA_PORT"],project,config["EMBEDDING_MODEL"],config["GOOGLE_API_KEY"])
        self.__graphStore = GraphDb(config["NEO4J_URI"],config["NEO4J_USER"],config["NEO4J_PASSWORD"],project)
        self.__llm = ChatGoogleGenerativeAI(
            model=config["CHAT_MODEL"],
            google_api_key=config["GOOGLE_API_KEY"]
        )

        # Create the retrieval chain - cleanest approach with dict unpacking
        self.__hybrid_rag_chain = (
            (lambda x: {**self.__hybrid_retrieval(x), "question": x})
            | self.__rag_prompt
            | self.__llm
            | StrOutputParser()
        )
    
    def __create_hybrid_context(self, chroma_docs: str, neo4j_context: str) -> Dict[str, str]:
        """Combine ChromaDB and Neo4j contexts"""
        graph_context, doc_context= "", ""
        if neo4j_context:
            graph_context = neo4j_context
        
        if chroma_docs:
            doc_context = chroma_docs
        
        return {
            "graph_context": graph_context,
            "doc_context": doc_context
        }

    def __hybrid_retrieval(self, question: str):
        vectorData = self.__vectorStore.retrieve_with_metadata(question)
        cypherQuery = self.__graphStore.retrieve(self.__llm, question, vectorData["content"], vectorData["metadata"]["relatedNodeIds"])
        return self.__create_hybrid_context(vectorData["content"], cypherQuery)
    
    def getRagChain(self):
        return self.__hybrid_rag_chain
    
    def getVectorStore(self):
        return self.__vectorStore
        