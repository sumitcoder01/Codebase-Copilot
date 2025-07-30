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
    plan: List[str]
    last_agent_output: str

def supervisor_node(state: AgentState) -> dict:
    log.info("Supervisor/Planner running...")
    llm = get_llm()
    last_human_message = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            last_human_message = message.content
            break
    if not last_human_message:
        return {"plan": []}

    prompt = SUPERVISOR_PROMPT.format(messages=last_human_message)
    supervisor_chain = llm | (lambda x: x.content.strip())
    response = supervisor_chain.invoke(prompt)
    log.info(f"Raw supervisor response: '{response}'")

    if "Finish" in response or not response:
        return {"plan": []}
    
    plan = [agent.strip() for agent in response.split(",") if agent.strip()]
    log.info(f"Supervisor created a plan: {plan}")
    return {"plan": plan, "last_agent_output": last_human_message}

def agent_node(state: AgentState, agent_name: str) -> dict:
    """The agent node now receives the agent_name directly."""
    session_id = state['session_id']
    log.info(f"Executing agent '{agent_name}' for session '{session_id}'")
    agent_executor = create_agent(session_id, agent_name)
    
    contextual_input = (
        f"Original user query: {state['messages'][0].content}\n\n"
        f"Context from previous step:\n{state['last_agent_output']}"
    )

    response = agent_executor.invoke({
        "messages": [HumanMessage(content=contextual_input)]
    })
    
    ai_message = response["messages"][-1]
    log.info(f"Agent '{agent_name}' produced output.")
    
    # We pass the agent name along with the output for the streamer.
    return {"messages": [ai_message], "last_agent_output": ai_message.content, "agent_name": agent_name}

def plan_router(state: AgentState) -> str:
    """The router now directly calls the agent node with the correct name."""
    if state["plan"]:
        # Pop the next agent from the plan
        next_agent_name = state["plan"].pop(0)
        # Return that name as the key for the conditional edge
        return next_agent_name
    else:
        return "END"

def create_graph() -> StateGraph:
    log.info("Creating LangGraph with a multi-step planner...")
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    
    # Create a unique node for each agent
    agent_names = ["QA_Agent", "Debug_Agent", "Refactor_Agent", "Diagram_Agent"]
    for name in agent_names:
        # The lambda function captures the 'name' for each node
        workflow.add_node(name, lambda state, name=name: agent_node(state, name))

    workflow.set_entry_point("supervisor")
    
    # The supervisor's output is routed by the plan_router
    workflow.add_conditional_edges(
        "supervisor",
        plan_router,
        {name: name for name in agent_names} | {"END": END}
    )
    
    # After each agent runs, it loops back to the plan_router to continue or end
    for name in agent_names:
        workflow.add_conditional_edges(
            name,
            plan_router,
            {name: name for name in agent_names} | {"END": END}
        )
    
    log.info("Multi-step graph created successfully.")
    return workflow

graph_app = create_graph().compile(checkpointer=MemorySaver())
log.info("Graph compiled successfully.")

def stream_graph(session_id: str, query: str):
    log.info(f"Streaming graph for session '{session_id}' with query: '{query}'")
    graph_input = {
        "messages": [HumanMessage(content=query)], "session_id": session_id,
        "plan": [], "last_agent_output": "",
    }
    config = {"configurable": {"thread_id": session_id}}
    
    output_generated = False
    for event in graph_app.stream(graph_input, config=config):
        # We now look for any of the agent nodes
        agent_names = ["QA_Agent", "Debug_Agent", "Refactor_Agent", "Diagram_Agent"]
        for name in agent_names:
            if name in event:
                node_output = event[name]
                if messages := node_output.get("messages"):
                    output_generated = True
                    # The agent name is now reliably in the output
                    agent_name = node_output.get('agent_name', 'Agent')
                    yield f"### Output from {agent_name} ###\n\n" + messages[-1].content + "\n\n---\n\n"
                    break # Move to the next event
    
    if not output_generated:
        log.warning("Graph execution finished with no agent output.")
        yield "The request was processed, but no valid plan was created. Please try rephrasing your request."