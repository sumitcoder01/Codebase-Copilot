import logging
import operator
from typing import TypedDict, List, Annotated

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.llm import get_llm
from app.agents import create_agent
from app.agents.prompts import SUPERVISOR_PROMPT

log = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    next: str

def supervisor_node(state: AgentState) -> dict:
    log.info(f"Supervisor running for session: {state['session_id']}")
    llm = get_llm()
    last_human_message = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            last_human_message = message.content
            break
    if not last_human_message:
        return {"next": "END"}
    
    prompt = SUPERVISOR_PROMPT.format(messages=last_human_message)
    supervisor_chain = llm | (lambda x: x.content.strip())
    next_agent_name = supervisor_chain.invoke(prompt)

    log.info(f"Supervisor decided next step is: '{next_agent_name}'")
    
    if "QA_Agent" in next_agent_name:
        return {"next": "QA_Agent"}
    elif "Debug_Agent" in next_agent_name:
        return {"next": "Debug_Agent"}
    elif "Refactor_Agent" in next_agent_name:
        return {"next": "Refactor_Agent"}
    elif "Diagram_Agent" in next_agent_name:
        return {"next": "Diagram_Agent"}
    else:
        return {"next": "END"}

def agent_node(state: AgentState) -> dict:
    agent_name = state['next']
    session_id = state['session_id']
    log.info(f"Executing agent '{agent_name}' for session '{session_id}'")
    agent_executor = create_agent(session_id, agent_name)
    response = agent_executor.invoke({
        "messages": [HumanMessage(content=state['messages'][-1].content)]
    })
    ai_message = response["messages"][-1]
    log.info(f"Agent '{agent_name}' produced output for session '{session_id}'")
    return {"messages": [ai_message]}

def create_graph() -> StateGraph:
    """
    Creates the graph with a linear, non-looping workflow.
    Supervisor -> Agent -> END
    """
    log.info("Creating LangGraph graph...")
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("agent_node", agent_node)
    
    def router(state: AgentState) -> str:
        if state["next"] == "END":
            return "END"
        return "agent_node"
        
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        router,
        { "agent_node": "agent_node", "END": END }
    )
    
    # *** THE DEFINITIVE FIX TO THE LOOP ***
    # Instead of looping back to the supervisor, we end the graph run
    # after the agent has produced its output.
    workflow.add_edge("agent_node", END)
    
    log.info("Graph created successfully with a non-looping structure.")
    return workflow

# --- The rest of the file is the same ---

graph_app = create_graph().compile(checkpointer=MemorySaver())
log.info("Graph compiled successfully with memory saver.")

def stream_graph(session_id: str, query: str):
    log.info(f"Streaming graph for session '{session_id}' with query: '{query}'")
    graph_input = {
        "messages": [HumanMessage(content=query)],
        "session_id": session_id,
    }
    config = {"configurable": {"thread_id": session_id}}
    for event in graph_app.stream(graph_input, config=config):
        if "agent_node" in event:
            node_output = event["agent_node"]
            if messages := node_output.get("messages"):
                yield messages[-1].content