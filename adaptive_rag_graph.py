# Code template from Eden Marcos with updates to latest LG and LC version
# This implements adaptive RAG - we are still using self-rag.
# there is an initial node that decides whether or not to use RAG or web search.
# the rest of the flow is the same

"""

Adaptive RAG -> Self-RAG

Flow of Adapative RAG:
* Graph takes a user input, aka the question
* LLM from route function, question_router
* LLM returns a decision
* use decision flows, conditional edge flows to set the next flow based on the response
* Eden did not put a node for the route but I did below for clarity.

Flow of Self-RAG:
♻️ If hallucinating: Try generating again with same docs
🌐 If off-topic: Go search the web for better docs
✅ If good answer: We're done!

"""

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
# From LangGraph family
from graph.state import GraphState

from graph.chains.answer_grader import answer_grader
from graph.chains.hallucination_grader import hallucination_grader
from graph.chains.router import question_router, RouteQuery
from graph.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEBSEARCH
from graph.nodes import generate, grade_documents, retrieve, web_search

# LangGraph core.
# After LC version 0.2.0+, it's recommended to use SG
from langgraph.graph import StateGraph, END, START 

load_dotenv()
memory = SqliteSaver.from_conn_string(":memory:")
memory = MemorySaver()


def decide_to_generate(state):
    """
    Decides whether to generate an answer or do web search based on current state.
    Returns either WEBSEARCH or GENERATE as the next node.
    """
    print("---ASSESS GRADED DOCUMENTS---")

    if state["web_search"]:
        print(
            "---DECISION: NOT ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, INCLUDE WEB SEARCH---"
        )
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE---")
        return GENERATE


def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    """
    Two-step grading process:
    1. Check if generation is grounded in documents (no hallucinations)
    2. Check if generation actually answers the question
    Returns: "useful", "not useful", or "not supported"
    """
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )

    if hallucination_grade := score.binary_score:
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        if answer_grade := score.binary_score:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"


def route_question(state: GraphState) -> str:
    """
    Decides initial path: web search or vector store retrieval
    Returns either WEBSEARCH or RETRIEVE as the starting point
    """
    print("---ROUTE QUESTION---")
    question = state["question"]
    source: RouteQuery = question_router.invoke({"question": question})
    if source.datasource == WEBSEARCH:
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return RETRIEVE

# Connect everything together:
workflow = StateGraph(GraphState)

# Add all nodes including the router node
workflow.add_node("ROUTE_SEARCH_OR_RETRIEVAL", route_question)  # Add routing as a visible node
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, web_search)

# Set ROUTE as the entry point. This tells LG by default to connect from START -> ROUTE
workflow.set_entry_point("ROUTE_SEARCH_OR_RETRIEVAL")

# Add conditional edges from ROUTE node to either WEBSEARCH or RETRIEVE
# This first decision flow illustrates ADAPATIVE RAG! The LLM makes a decision. 
workflow.add_conditional_edges(
    "ROUTE_SEARCH_OR_RETRIEVAL",
    route_question,
    { # LEFT - RETURN RESULT, RIGHT = GO TO THIS NODE
        WEBSEARCH: WEBSEARCH,
        RETRIEVE: RETRIEVE,
    }
)

# Rest of the edges remain the same
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    { # LEFT - RETURN RESULT, RIGHT = GO TO THIS NODE
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)
workflow.add_edge(WEBSEARCH, GENERATE)
workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    { # LEFT - RETURN RESULT, RIGHT = GO TO THIS NODE
        "not supported": GENERATE,
        "useful": END,
        "not useful": WEBSEARCH,
    },
)

app = workflow.compile(checkpointer=memory)
app.get_graph().draw_mermaid_png(output_file_path="adapative-rag-graph.png")
