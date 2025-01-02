############################################
#  🎯 LANGGRAPH ULTIMATE CHEAT SHEET 🎯   #
############################################

"""
⚠️ DEPENDENCY VERSIONS (as of March 2024):
This cheatsheet was tested with:
- langgraph==0.2.60
- langchain==0.3.13
- langchain-community==0.3.13
- langchain-core==0.3.28
- langchain-openai==0.2.14
- langchain-chroma==0.1.4
- chromadb==0.5.0
- openai>=1.0.0
- python-dotenv==1.0.1
- tiktoken==0.7.0
- tavily-python==0.5.0


Note: Breaking changes may occur in newer versions.
See requirements.txt for full dependency list.

It's highly recommended to check dependency issues, and use GenAI to fix these issues.
"""

# IMPORT STATEMENTS:

# Type hints
from typing import TypedDict, List, Dict

# LangGraph core
from langgraph.graph import StateGraph, END, START
from langgraph_checkpoint_sqlite import SqliteSaver

# LangChain core and models
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Vector store and embeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Text processing
from langchain_text_splitters import RecursiveCharacterTextSplitter

"""
🔑 KEY CONCEPTS:
- Think of LangGraph like an assembly line
- State = blueprint for data format
- Nodes = workers that process data
- Edges = paths between workers
"""


"""
###########################################
# 0. 📦 INSTALLATION & DEPENDENCIES
###########################################

# Core dependencies
pip install langgraph    # The main LangGraph package
pip install langchain   # Required for most LangGraph functionality
pip install langchain-community  # For community tools like Tavily

# Common additional dependencies
pip install python-dotenv   # For loading .env files
pip install openai         # If using OpenAI models
pip install chromadb       # If using vector storage
pip install tavily-python  # If using Tavily search

# Optional but useful
pip install tiktoken       # For token counting
pip install numpy         # Often needed for vector operations
pip install pandas        # If working with structured data

💡 TIPS:
- Use a virtual environment (venv)
- Install only what you need
- Check versions are compatible

"""


###########################################
# 1. 📋 RETRIEVER SETUP
###########################################

"""
RETRIEVER COMPONENTS:
1. Embeddings: Convert text to vectors
2. Text Splitter: Break documents into chunks
3. Vector Store: Store and search embeddings
4. Retriever: Interface for similarity search
"""

# Initialize core components
embeddings = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

def setup_retriever(documents: List[str]):
    """Basic RAG retriever setup"""
    # 1. Split into chunks
    splits = text_splitter.split_text("\n\n".join(documents))
    
    # 2. Create vector store
    vectorstore = Chroma.from_texts(
        texts=splits,
        embedding=embeddings,
        collection_name="my_documents"
    )
    
    # 3. Create retriever interface
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    return retriever

# Example documents for testing
sample_docs = [
    """LangGraph is a library for building stateful, multi-step applications with LLMs.
    It helps create workflows where different components work together to solve complex tasks.""",
    
    """Key features of LangGraph include:
    - State management
    - Conditional branching
    - Cyclical workflows
    - Integration with LangChain""",
    
    """Common use cases for LangGraph:
    - Multi-step reasoning
    - Conversational agents
    - Research assistants
    - Document analysis pipelines"""
]

# Initialize retriever with samples
retriever = setup_retriever(sample_docs)

"""
💡 RETRIEVER TIPS:
1. Configuration:
   - Adjust chunk_size based on model context window
   - Increase overlap for better context preservation
   - Use k parameter to control number of results

2. Best Practices:
   - Store embeddings for reuse
   - Consider MMR for diverse results
   - Filter results when needed
   - Regularly update document store

3. Common Issues:
   - Large chunks may exceed token limits
   - Small chunks may lose context
   - Embeddings cost money - cache when possible
"""

###########################################
# 2. 📋 STATE: The Data Blueprint
###########################################

# Before you do anything, define the llm:
llm = ChatOpenAI(temperature=0)

class GraphState(TypedDict):
    # Everything your graph needs to know/remember
    question: str          # Original question
    documents: List[str]   # Retrieved documents
    web_search: bool      # Whether to search web
    
"""
💡 TIPS:
- State is like a contract all nodes must follow
- Define ALL fields your graph might need
- Every node will see this same state structure
"""

###########################################
# 3. 🔄 NODES: The Workers
###########################################
def my_node(state: GraphState) -> Dict:
    # 1. Get what you need from state
    question = state["question"]
    
    # 2. Do some work
    result = do_something(question)
    
    # 3. Return ONLY what changed
    return {"documents": result}

"""
💡 TIPS:
- Nodes MUST take state as input
- Nodes MUST return a dictionary
- Only return fields that changed
- Can access any field in state
"""

###########################################
# 4. 🏭 SIMPLE EXAMPLE: Q&A Graph
###########################################
# Define simple state
class SimpleGraphState(TypedDict):
    question: str
    answer: str

# Define simple node with proper LLM usage
def get_answer(state: SimpleGraphState) -> Dict:
    question = state["question"]
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant."),
        ("user", "{question}")
    ])
    
    # Create chain and invoke
    chain = prompt | llm
    answer = chain.invoke({"question": question})
    
    return {"answer": answer.content}

# Setup simple graph
simple_graph = StateGraph(SimpleGraphState)

# Add nodes and edges
simple_graph.add_node("qa_start", get_answer)  # More descriptive name
simple_graph.set_entry_point("qa_start")       # Updated entry point
simple_graph.add_edge("qa_start", END)

# Run simple graph
simple_chain = simple_graph.compile()
result = simple_chain.invoke({
    "question": "What is LangGraph?",
    "answer": ""  # Must include all fields!
})

# Export graph visualizations
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

# 1. Get Mermaid syntax
print(simple_chain.get_graph().draw_mermaid())

# 2. Save as PNG using Mermaid.ink API
display(
    Image(
        simple_chain.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
            curve_style=CurveStyle.LINEAR,
            node_colors=NodeStyles(first="#ffdfba", last="#baffc9", default="#fad7de")
        )
    )
)

"""
💡 TIPS:
- Every graph needs an entry point (start node)
- Use set_entry_point() to define where flow begins
- Initial state needs ALL fields
- Use to_mermaid() and to_mermaid_png() with proper MermaidDrawMethod
"""

###########################################
# 5. 🌟 COMPLEX EXAMPLE: RAG with Search
###########################################
# Define rich state
class ComplexGraphState(TypedDict):
    question: str
    documents: List[str]
    web_search: bool
    final_answer: str
    search_attempts: int

# Define multiple nodes
def retrieve_docs(state: ComplexGraphState) -> Dict:
    docs = retriever.get_relevant_documents(state["question"])
    doc_strings = [doc.page_content for doc in docs]
    return {"documents": doc_strings}

def check_docs(state: ComplexGraphState) -> Dict:
    if not state["documents"]:
        return {"web_search": True}
    return {"web_search": False}

def web_search(state: ComplexGraphState) -> Dict:
    results = search_web(state["question"])
    return {
        "documents": results,
        "search_attempts": state["search_attempts"] + 1
    }

def generate_answer(state: ComplexGraphState) -> Dict:
    try:
        # Create a RAG prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Use the following documents to answer the question. "
                      "If you can't find the answer, say so."),
            ("user", "Documents: {documents}\n\nQuestion: {question}")
        ])
        
        # Debug print
        print(f"State in generate_answer: {state}")
        
        # Create chain and invoke with proper error handling
        chain = prompt | llm
        response = chain.invoke({
            "question": state.get("question", "No question provided"),
            "documents": "\n".join(state.get("documents", [])) or "No documents available."
        })
        
        return {"final_answer": response.content}
    except KeyError as e:
        print(f"KeyError in generate_answer: {e}")
        print(f"Current state: {state}")
        raise

# Setup complex graph
complex_graph = StateGraph(ComplexGraphState)

# Add all nodes
complex_graph.add_node("rag_start", retrieve_docs)      # More descriptive name
complex_graph.add_node("check", check_docs)
complex_graph.add_node("search", web_search)
complex_graph.add_node("answer", generate_answer)

# Set entry point
complex_graph.set_entry_point("rag_start")              # Updated entry point

# Add conditional routing
complex_graph.add_edge("rag_start", "check")           # Updated edge
complex_graph.add_conditional_edges(
    "check",
    lambda x: "search" if x["web_search"] else "answer"
)
complex_graph.add_edge("search", "check")
complex_graph.add_edge("answer", END)

# Run complex graph with complete state
complex_chain = complex_graph.compile()
initial_state = {
    "question": "What's new in AI?",
    "documents": [],
    "web_search": False,
    "final_answer": "",
    "search_attempts": 0
}

# Debug print before invoking
print(f"Initial state: {initial_state}")
result = complex_chain.invoke(initial_state)

# Export complex graph visualizations
# 1. Get Mermaid syntax
print(complex_chain.get_graph().draw_mermaid())

# 2. Save as PNG using Mermaid.ink API
display(
    Image(
        complex_chain.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
            curve_style=CurveStyle.LINEAR,
            node_colors=NodeStyles(first="#ffdfba", last="#baffc9", default="#fad7de")
        )
    )
)

"""
💡 TIPS FOR COMPLEX GRAPHS:
- Always set an entry point with set_entry_point()
- First node should be named "start" (convention)
- Break into logical nodes
- Use conditional edges for branching
- Can create loops (web_search → check)
- Track state for complex flows
- IMPORTANT: Initial state must include ALL fields defined in TypedDict, but each field only once!
"""

###########################################
# 6. 🚨 COMMON GOTCHAS & SOLUTIONS
###########################################
"""
1. State Issues:
   - MUST match TypedDict exactly
   - ALL fields required in initial state
   - Can't add new fields on the fly

2. Node Issues:
   - MUST return dictionary always
   - Only return what changed
   - Can read any state field

3. Edge Issues:
   - Don't forget END
   - Conditional edges need all paths covered
   - Check for infinite loops

4. Running Issues:
   - Always compile before invoke
   - Check initial state has all fields
   - Debug by printing state in nodes
"""

# ###########################################
# # 7. 🔍 DEBUGGING TIPS
# ###########################################
# def debug_node(state: GraphState):
#     print(f"Current state: {state}")
#     # ... do work ...
#     return {"some_update": new_value}

# # Add debug nodes between other nodes
# graph.add_node("debug", debug_node)

# """
# 💡 FINAL TIPS:
# - Start simple, add complexity gradually
# - Test each node independently
# - Print state often while debugging
# - Remember: nodes are just functions!
# """