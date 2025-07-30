import logging
from typing import List
from langchain.agents import AgentExecutor
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage

from app.llm import get_llm
from app.tools import ReadFileTool, get_retriever_tool, ListFilesTool

log = logging.getLogger(__name__)

def create_agent(session_id: str, agent_type: str) -> AgentExecutor:
    """
    Factory function to create a specific type of ReAct agent.
    This version includes much stricter instructions to enforce a separation of concerns.
    """
    log.info(f"Creating agent of type '{agent_type}' for session '{session_id}'")
    llm = get_llm()
    tools: List[BaseTool] = []
    instructions = ""

    # Common tools for exploration
    list_tool = ListFilesTool(session_id=session_id)
    read_tool = ReadFileTool(session_id=session_id)

    tool_usage_instructions = (
        "To find the correct file path, you MUST use the 'list_files' tool first. "
        "Examine the output of 'list_files' to determine the full, correct path to a file. "
        "When you use 'read_file', you MUST provide the complete, relative path you discovered."
    )

    if agent_type == "QA_Agent":
        instructions = (
            "You are a Q&A expert. Your ONLY job is to answer questions about the codebase. "
            "Do NOT suggest refactoring or debugging. "
            f"{tool_usage_instructions} After exploring the files, use the 'codebase_retriever' "
            "tool to find relevant code snippets to answer the user's question."
        )
        tools.extend([list_tool, get_retriever_tool(session_id)])

    elif agent_type == "Debug_Agent":
        instructions = (
            "You are a debugging expert. Your ONLY job is to analyze a file for bugs, vulnerabilities, and code smells. "
            "You MUST NOT refactor or rewrite the code. Your output must be a clear, formatted report of your findings. "
            "This report will be passed to the Refactor_Agent. "
            f"{tool_usage_instructions}"
        )
        tools.extend([list_tool, read_tool])

    elif agent_type == "Refactor_Agent":
        instructions = (
            "You are a code refactoring specialist. You will receive context from the Debug_Agent that describes issues in a file. "
            "Your ONLY job is to rewrite and improve the code based on the provided report. "
            f"{tool_usage_instructions} Present the complete, refactored code for the file."
        )
        tools.extend([list_tool, read_tool])
    
    elif agent_type == "Diagram_Agent":
        instructions = (
            "You are a software architecture visualizer. Your ONLY job is to create diagrams. "
            f"{tool_usage_instructions} After reading files to understand the logic, "
            "your output MUST ONLY be the Mermaid.js code block for the diagram. Do not add any other explanation."
        )
        tools.extend([list_tool, read_tool])

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    system_message = SystemMessage(content=instructions)
    
    agent_executor = create_react_agent(llm, tools, prompt=system_message)
    log.info(f"Agent '{agent_type}' created successfully for session '{session_id}'.")
    
    return agent_executor