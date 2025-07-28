import logging
import operator 
from typing import TypedDict, List, Annotated
from operator import itemgetter

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.llm import get_llm
from app.agents import create_agent
from app.agents.prompts import SUPERVISOR_PROMPT

log = logging.getLogger(__name__)

# --- 1. Define the State for the Graph ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]  
    session_id: str
    next: str

# --- 2. Define the Nodes of the Graph ---

def supervisor_node(state: AgentState) -> dict:
    log.info(f"Supervisor running for session: {state['session_id']}")
    llm = get_llm()
    
    prompt = PromptTemplate.from_template(SUPERVISOR_PROMPT).format(
        messages='\n'.join([f"{msg.type}: {msg.content}" for msg in state['messages']])
    )
    
    supervisor_chain = llm | (lambda x: x.content)
    next_agent_name = supervisor_chain.invoke(prompt)

    log.info(f"Supervisor decided next step is: '{next_agent_name}'")
    
    if "finish" in next_agent_name.lower():
        return {"next": "END"}
        
    return {"next": next_agent_name}

def agent_node(state: AgentState) -> dict:
    agent_name = state['next']
    session_id = state['session_id']
    log.info(f"Executing agent '{agent_name}' for session '{session_id}'")

    last_message = state['messages'][-1].content
    
    agent_executor = create_agent(session_id, agent_name)
    
    response = agent_executor.invoke({
        "input": last_message,
        "chat_history": state['messages']
    })
    
    ai_message = AIMessage(content=response["output"])
    log.info(f"Agent '{agent_name}' produced output for session '{session_id}'")
    
    return {"messages": [ai_message]}

# --- 3. Define the Edges and Assemble the Graph ---

def create_graph() -> StateGraph:
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
        {"agent_node": "agent_node", "END": END}
    )
    
    workflow.add_edge("agent_node", "supervisor")
    
    log.info("Graph created successfully.")
    return workflow

# --- 4. Compile the Graph ---
graph_app = create_graph().compile(checkpointer=MemorySaver())
log.info("Graph compiled successfully with memory saver.")

# --- Helper function for streaming ---
def stream_graph(session_id: str, query: str):
    log.info(f"Streaming graph for session '{session_id}' with query: '{query}'")
    
    graph_input = {
        "messages": [HumanMessage(content=query)],
        "session_id": session_id,
    }
    
    config = {"configurable": {"thread_id": session_id}}

    for event in graph_app.stream(graph_input, config=config):
        for value in event.values():
            if isinstance(value.get("messages", [])[-1], AIMessage):
                yield value["messages"][-1].content