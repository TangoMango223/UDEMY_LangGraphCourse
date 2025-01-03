from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    input: str
    user_feedback: str


def step_1(state: State) -> None:
    print("---Step 1---")


def human_feedback(state: State) -> None:
    print("---human_feedback---")


def step_3(state: State) -> None:
    print("---Step 3--")


builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("human_feedback", human_feedback)
builder.add_node("step_3", step_3)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "human_feedback")
builder.add_edge("human_feedback", "step_3")
builder.add_edge("step_3", END)

# # set up the memory
# memory = SqliteSaver.from_conn_string("checkpoints.sqlite")

# option 1 - use the built-in memory:
memory = MemorySaver()

graph = builder.compile(checkpointer=memory, interrupt_before=["human_feedback"])

graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

if __name__ == "__main__":
    
    # Define thread for tracking graph state
    thread = {"configurable": {"thread_id": "777"}}

    initial_input = {"input": "hello world"}

    # when we live-stream, only VALUES or final output of each node will be returned
    # This begins the execution of the graph
    for event in graph.stream(initial_input, thread, stream_mode="values"):
        print(event)

    # # Displays the next node in the thread, which is human feedback
    # print(graph.get_state(thread).next)

    user_input = input("Tell me how you want to update the state: ")
    
    # get next node using get_state() moving to next node
    
    # If we don't continue calling, the graph will stop here and not continue.
    # We need to update stream, as if the graph was running normall
    # This overrides user_feedback param from the StateGraph in the beginning
    
    graph.update_state(thread, {"user_feedback": user_input}, as_node="human_feedback")
    
    # ----
    print("--State after update--")
    # See the entire state from this modification
    print(graph.get_state(thread))
    
    print("-----")

    # # See next node
    # print(graph.get_state(thread).next)
    
    print("---Resuming Run ---")
    # Resume call of for-loop, otherwise the graph will not continue.
    # None - continue where we left off
    # for event in graph.stream(None, thread, stream_mode="values"):
    #     print(event)
    
    # You can also continue the rest manually without a for loop here.
    print(graph.get_state(thread).next)
    next_event = graph.stream(None, thread, stream_mode="steps")
    
        # 2. Using next() to get one event at a time
    # events = graph.stream(None, thread, stream_mode="values")
    # event = next(events)  # Get first event
    # event = next(events)  # Get next event

    
    # Why take this approach:
    # Async run with interrupt allowed
    # Not waiting on this one action of human input
    # Graph can handle error recovery