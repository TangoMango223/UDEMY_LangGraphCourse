# Use SqLite3 database!

import sqlite3
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    input: str
    user_feedback: str

# Initialize all the function nodes

def step_1(state: State) -> None:
    print("---Step 1---")


def human_feedback(state: State) -> None:
    print("---human_feedback---")


def step_3(state: State) -> None:
    print("---Step 3--")


# Create structure of the Graph
builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("human_feedback", human_feedback)
builder.add_node("step_3", step_3)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "human_feedback")
builder.add_edge("human_feedback", "step_3")
builder.add_edge("step_3", END)

# Create directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Connect to SQLite database in the data directory
conn = sqlite3.connect(
    "data/checkpoints.sqlite", # use this formula for local disk version
    # can put address of remote sqlite location
    check_same_thread=False
)

# Hypothetical path if remote sql location:
# conn = sqlite3.connect(
#     "file:///path/to/remote/checkpoints.sqlite",  # Unix/Linux
#     # OR
#     "file://server/share/checkpoints.sqlite",     # Network share
#     # OR
#     "file:///C:/path/to/remote/checkpoints.sqlite",  # Windows
#     uri=True,  # Important! Must set uri=True for remote connections
#     check_same_thread=False
# )

# initialize memory object with sqlite3
memory = SqliteSaver(conn)

# Why use the checkpoint integration from LangGraph?
# It sets up all the tables and format for saving, for you:

# -- Simplified view of what LangGraph stores
# CREATE TABLE checkpoints (
#     thread_id TEXT,        -- Track different executions
#     checkpoint_id TEXT,    -- Unique identifier for each save
#     node_name TEXT,        -- Which node we're at
#     state_data TEXT,       -- The actual state (JSON)
#     timestamp DATETIME,    -- When it was saved
#     ...
# );

# ----- Compile the graph and draw mermaid  -----

graph = builder.compile(checkpointer=memory, interrupt_before=["human_feedback"])

graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

# ------ Main Control ------ 

if __name__ == "__main__":
    thread = {"configurable": {"thread_id": "777"}}

    initial_input = {"input": "hello world"}

    for event in graph.stream(initial_input, thread, stream_mode="values"):
        print(event)

    print(graph.get_state(thread).next)

    user_input = input("Tell me how you want to update the state: ")

    graph.update_state(thread, {"user_feedback": user_input}, as_node="human_feedback")

    print("--State after update--")
    print(graph.get_state(thread))

    print(graph.get_state(thread).next)

    for event in graph.stream(None, thread, stream_mode="values"):
        print(event)
        
        
# Sample Code for MYSQL setup:

# --- Production (MySQL) ---
# # Robust, Remote, Multi-user
# from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

# DB_URI = "mysql://user:password@production-server:3306/database"
# checkpointer = PyMySQLSaver.from_conn_string(DB_URI)
# checkpointer.setup()

# graph = builder.compile(checkpointer=checkpointer)