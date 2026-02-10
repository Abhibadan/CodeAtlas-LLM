from dbModule.VectorDb import VectorDb
from dbModule.GraphDb import GraphDb
from dbModule import Conversation
from bson import ObjectId
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import (
    chroma_config, 
    neo4j_config
)
from components.aiModelAdapter import AIModelFactory
from typing import List, Dict, Any
from components.tools import AgentTools
from langchain.agents import create_agent
class RagAgent:
    prompt = """You are an expert code analysis assistant with access to specialized tools for querying codebases.
        You are provided with a code knowledge graph and a vector store of code documentation.
        
        TOOLS AVAILABLE:
        You have access to two powerful tools:
        1. **vector_search** - Search code documentation and retrieve relevant node IDs
        2. **get_graph_schema** - Get the neo4j schema of the code knowledge graph 
        3. **graph_query** - Neo4j graph query tool to retrieve code relationships, dependencies, and structure using proper cypher query

        GUIDELINES FOR TOOL USAGE:
        1. For questions about code documentation, functions, or general information:
        → Use vector_search first to find relevant documentation and node IDs

        2. For questions about dependencies, relationships, or code structure:
        → Use get_graph_schema first to get the schema of the code knowledge graph
        → Use the schema to generate a cypher query based on the user's question
        → Use graph_query with the generated cypher query for detailed relationship analysis

        3. BEST PRACTICE - Sequential Tool Calls:
        - Call vector_search to get relevant node IDs and documentation
        - Extract the "relatedNodeIds" from the vector_search result
        - Use get_graph_schema to get the schema of the code knowledge graph
        - Generate a cypher query based on the user's question using the schema
        - Pass the generated cypher query to graph_query tool

        4. When to skip tools:
        - For simple conceptual questions that don't require codebase data
        - For general programming questions not specific to this codebase

        YOUR RESPONSIBILITIES:
        1. **Code Understanding**: Explain code functionality at various levels (module, class, function)
        2. **Code Summarization**: Provide concise overviews highlighting key functionalities
        3. **Modification Guidance**: Suggest improvements with clear rationale and step-by-step instructions
        4. **Impact Analysis**: Identify affected components and cascading effects through dependencies
        5. **Provide Code Snippets**: When asked, extract and display source code from the tool results

        IMPORTANT RULES:
        - Base all analysis on data retrieved from tools
        - Use the relatedNodeIds as eid in the cypher query
        - For better results, combine exact eid matching with regex pattern matching on fields like name, type, kind, sourceCode, etc. using OR clauses
        - Don't mention internal node IDs (i.e. eid, id, etc.) in your responses to users
        - If source code is in the graph results (property 'sourceCode'), include it when relevant
        - Consider the entire dependency chain when suggesting modifications
        - Flag potential breaking changes and side effects
        - Use the chat history to provide context to the user
        

        CODE FORMATTING:
        When providing code examples, use markdown format:
        ```language
        ... code here ...
        ```
        Where 'language' is the programming language (python, javascript, typescript, etc.)

        RESPONSE STRUCTURE:
        - Start with a direct answer to the user's query
        - Use tool results to provide evidence and context
        - Provide code snippets when relevant (extract from 'sourceCode' property in results)
        - Explain relationships and dependencies when applicable
        - Keep explanations clear, technical, and concise
        - Use natural prose; avoid excessive bullet points unless requested

        TONE:
        - Clear, precise, and technical
        - Confident but acknowledge limitations
        - Focus on actionable insights
        """


    def __init__(self,data):
        # Create adapter for the selected provider
        ai_adapter = AIModelFactory.create_adapter()
        
        # Initialize vector store with adapter's embedding model
        embeddings = ai_adapter.get_embeddings()
        self.__vectorStore = VectorDb(
            chroma_config["host"],
            chroma_config["port"],
            data["project"],
            embeddings
        )
        
        self.__graphStore = GraphDb(neo4j_config["uri"],neo4j_config["user"],neo4j_config["password"],data["project"])
        self.__chatId = ObjectId(data["chatId"])
        self.__convId = data.get("convId",None)
        self.__use_chat_history = data.get("use_chat_history", True)
        
        # Get chat model from adapter
        self.__llm = ai_adapter.get_chat_model()
        
        # Create tools
        agent_tools = AgentTools(self.__vectorStore, self.__graphStore, self.__llm)
        self.__tools = agent_tools.get_tools()

        self.prompt = self.prompt.format(chat_history=self.__get_chat_history())
        print(self.prompt)
        # Create agent with tools using the correct API
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt),
            ("human", "{question}"),
        ])
        self.__agent_executor = create_agent(
            model=self.__llm,
            tools=self.__tools,
            prompt=rag_prompt,
            debug=True  # Enable verbose output
        )
    
    def __get_chat_history(self) -> str:
        """Retrieve chat history for context"""
        if self.__convId:
            chatHistory = Conversation.find_by_id(ObjectId(self.__convId))
        elif self.__use_chat_history:
            chatHistory = Conversation.find_by_chat_id(self.__chatId, limit=6)
        else:
            chatHistory = []
        
        return "\\n".join([f"{msg['role']}: {msg['content']}" for msg in chatHistory])
    
    def getRagChain(self):
        """Return a chain-like interface for backward compatibility"""
        def chain_stream(question: str):
            """Wrapper to make agent executor compatible with streaming interface"""
            # chat_history = self.__get_chat_history()
            
            # # Prepend chat history to question if available
            # full_input = question
            # if chat_history and self.__use_chat_history:
            #     full_input = f"Chat History:\n{chat_history}\n\nCurrent Question: {question}"
            
            # Run the agent
            result = self.__agent_executor.invoke({"messages": [{"role": "user", "content": "Hi"}]})
            print("Agent result:", result)
            
            # Extract the output from the agent's response
            # create_agent returns a state with messages
            if "messages" in result:
                messages = result["messages"]
                if messages:
                    # Get the last message content
                    last_message = messages[-1]
                    output = last_message.content if hasattr(last_message, 'content') else str(last_message)
                else:
                    output = "No response generated"
            else:
                # Fallback if format is different
                output = result.get("output", str(result))
            
            yield output
        
        # Create a simple object that has a stream method
        class ChainWrapper:
            def __init__(self, stream_func):
                self.stream_func = stream_func
            
            def stream(self, question: str):
                return self.stream_func(question)
        
        return ChainWrapper(chain_stream)
    
    def getVectorStore(self):
        return self.__vectorStore
        