import logging
from typing import List
from langchain.agents import AgentExecutor
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool

from app.llm import get_llm
from app.tools import ReadFileTool, get_retriever_tool
from .prompts import REACT_AGENT_PROMPT

log = logging.getLogger(__name__)

def create_agent(session_id: str, agent_type: str) -> AgentExecutor:
    """
    Factory function to create a specific type of ReAct agent.

    Args:
        session_id (str): The session ID to scope the tools.
        agent_type (str): The type of agent to create ('QA', 'Debug', 'Refactor', 'Diagram').

    Returns:
        AgentExecutor: A runnable agent executor instance.
    """
    log.info(f"Creating agent of type '{agent_type}' for session '{session_id}'")
    llm = get_llm()
    tools: List[BaseTool] = []
    instructions = ""

    # Configure tools and instructions based on agent type
    if agent_type == "QA_Agent":
        instructions = (
            "You are a Q&A expert. Your goal is to answer questions about the codebase. "
            "Use the 'codebase_retriever' tool to find relevant code snippets and answer the user's question."
        )
        tools.append(get_retriever_tool(session_id))

    elif agent_type == "Debug_Agent":
        instructions = (
            "You are a debugging expert. The user will ask you to find bugs in a specific file. "
            "Use the 'read_file' tool to get the file's content, then analyze it for bugs, "
            "vulnerabilities, and errors. Provide a detailed report of your findings."
        )
        tools.append(ReadFileTool(session_id=session_id))

    elif agent_type == "Refactor_Agent":
        instructions = (
            "You are a code refactoring specialist. The user will ask you to improve a file. "
            "Use the 'read_file' tool to get the file's content. "
            "Rewrite and improve the code, focusing on readability, efficiency, and best practices. "
            "Explain the key changes you made."
        )
        tools.append(ReadFileTool(session_id=session_id))
    
    elif agent_type == "Diagram_Agent":
        instructions = (
            "You are a software architecture visualizer. Your task is to create diagrams based on the user's request. "
            "If the user provides a file name, use the 'read_file' tool to understand its logic. "
            "Generate a diagram in Mermaid.js syntax that accurately represents the architecture or logic flow. "
            "ONLY output the Mermaid.js code block."
        )
        # Diagram agent might need to read files to understand the logic to be diagrammed
        tools.append(ReadFileTool(session_id=session_id))

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Create the final system prompt by injecting the specific instructions
    agent_prompt = REACT_AGENT_PROMPT.partial(instructions=instructions)
    
    # Use the LangGraph prebuilt function to create the ReAct agent
    agent_executor = create_react_agent(llm, tools, agent_prompt)
    log.info(f"Agent '{agent_type}' created successfully for session '{session_id}'.")
    
    return agent_executor