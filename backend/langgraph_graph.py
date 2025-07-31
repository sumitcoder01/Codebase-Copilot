import logging
import operator
import json
from typing import TypedDict, List, Annotated

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.llm import get_llm
from app.agents import create_agent
from app.agents.prompts import SUPERVISOR_PROMPT

log = logging.getLogger(__name__)

# --- 1. THE DEFINITIVE FIX FOR PARALLEL STATE ---

def _join_agent_outputs(a: str, b: str) -> str:
    """A custom reducer function to join the outputs of parallel agents.
    It MUST accept two arguments and return one."""
    return f"{a}\n\n{b}"

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    plan: List[List[str]]
    last_agent_output: Annotated[str, _join_agent_outputs]

# --- 2. Update agent_node to return a list for the reducer ---

def agent_node(state: AgentState, agent_name: str) -> dict:
    """A generic node that executes a single agent."""
    session_id = state['session_id']
    log.info(f"Executing agent '{agent_name}' for session '{session_id}'")
    agent_executor = create_agent(session_id, agent_name)
    
    contextual_input = (
        f"Original user query: {state['messages'][0].content}\n\n"
        f"Context from previous step(s):\n{state['last_agent_output']}"
    )

    response = agent_executor.invoke({
        "messages": [HumanMessage(content=contextual_input)]
    })
    
    ai_message = response["messages"][-1]
    output = f"### Output from {agent_name} ###\n\n{ai_message.content}"
    log.info(f"Agent '{agent_name}' produced output.")
    
    # The output is now a simple string, which the reducer will handle.
    return {"messages": [AIMessage(content=output)], "last_agent_output": output}
# --- The rest of the file is correct and does NOT need to be changed ---

def supervisor_node(state: AgentState) -> dict:
    log.info("Supervisor/Planner running...")
    llm = get_llm()
    last_human_message = state["messages"][-1].content
    prompt = SUPERVISOR_PROMPT.format(messages=last_human_message)
    supervisor_chain = llm | (lambda x: x.content.strip())
    response = supervisor_chain.invoke(prompt)
    log.info(f"Raw supervisor plan response: '{response}'")
    try:
        plan = json.loads(response.replace("'", '"'))
        if not isinstance(plan, list): raise ValueError
    except (json.JSONDecodeError, ValueError):
        log.warning("Supervisor did not produce a valid plan. Ending run.")
        return {"plan": []}
    log.info(f"Supervisor created a plan: {plan}")
    return {"plan": plan, "last_agent_output": last_human_message}

def plan_router(state: AgentState) -> List[str]:
    if not state["plan"]:
        log.info("Router: Plan is complete. Ending run.")
        return [END]
    next_step = state["plan"].pop(0)
    log.info(f"Router: Next step is to run agents: {next_step}")
    return next_step

def create_graph() -> StateGraph:
    log.info("Creating LangGraph with parallel execution capabilities...")
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    agent_names = ["QA_Agent", "Debug_Agent", "Refactor_Agent", "Diagram_Agent"]
    for name in agent_names:
        workflow.add_node(name, lambda state, name=name: agent_node(state, name))
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges("supervisor", plan_router, agent_names + [END])
    for name in agent_names:
        workflow.add_edge(name, "joiner")
    workflow.add_node("joiner", lambda state: {})
    workflow.add_conditional_edges("joiner", plan_router, agent_names + [END])
    log.info("Parallel graph created successfully.")
    return workflow

graph_app = create_graph().compile(checkpointer=MemorySaver())
log.info("Graph compiled successfully.")

def stream_graph(session_id: str, query: str):
    log.info(f"Streaming graph for session '{session_id}' with query: '{query}'")
    graph_input = {
        "messages": [HumanMessage(content=query)], "session_id": session_id,
        "plan": [], "last_agent_output": [],
    }
    config = {"configurable": {"thread_id": session_id}}
    output_generated = False
    for event in graph_app.stream(graph_input, config=config):
        agent_names = ["QA_Agent", "Debug_Agent", "Refactor_Agent", "Diagram_Agent"]
        for name in agent_names:
            if name in event:
                node_output = event[name]
                if messages := node_output.get("messages"):
                    output_generated = True
                    yield messages[-1].content + "\n\n---\n\n"
                    break
    if not output_generated:
        log.warning("Graph execution finished with no agent output.")
        yield "The request was processed, but no valid plan was created. Please try rephrasing."