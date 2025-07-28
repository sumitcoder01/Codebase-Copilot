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
    This version includes much stricter, more prescriptive instructions
    to improve the agent's reasoning and memory.
    """
    log.info(f"Creating agent of type '{agent_type}' for session '{session_id}'")
    llm = get_llm()
    tools: List[BaseTool] = []
    instructions = ""

    # Common tools for exploration
    list_tool = ListFilesTool(session_id=session_id)
    read_tool = ReadFileTool(session_id=session_id)

    # A common set of strict instructions for using tools
    tool_usage_instructions = (
        "To find the correct file path, you MUST use the 'list_files' tool first. "
        "Examine the output of 'list_files' to determine the full, correct path to a file. "
        "When you use 'read_file', you MUST provide the complete, relative path you discovered. "
        "For example: if 'list_files' returns 'src', your next step should be 'list_files' on 'src'. "
        "If that returns 'main.py', you must then use 'read_file' with the path 'src/main.py'."
    )

    if agent_type == "QA_Agent":
        instructions = (
            "You are a Q&A expert. Your goal is to answer questions about the codebase. "
            f"{tool_usage_instructions} After exploring the files, use the 'codebase_retriever' "
            "tool to find relevant code snippets and answer the user's question."
        )
        tools.extend([list_tool, get_retriever_tool(session_id)])

    elif agent_type == "Debug_Agent":
        instructions = (
            "You are a debugging expert. Your job is to find bugs in a specific file. "
            f"{tool_usage_instructions} Once you have read the file's content, analyze it for bugs, "
            "vulnerabilities, and errors, and provide a detailed report."
        )
        tools.extend([list_tool, read_tool])

    elif agent_type == "Refactor_Agent":
        instructions = (
            "You are a code refactoring specialist. Your job is to improve a file. "
            f"{tool_usage_instructions} Once you have read the file's content, rewrite and improve the code, "
            "focusing on readability, efficiency, and best practices. Explain the key changes you made."
        )
        tools.extend([list_tool, read_tool])
    
    elif agent_type == "Diagram_Agent":
        instructions = (
            "You are a software architecture visualizer. Your task is to create diagrams. "
            f"{tool_usage_instructions} After reading one or more files to understand the logic, "
            "generate a diagram in Mermaid.js syntax. ONLY output the Mermaid.js code block."
        )
        tools.extend([list_tool, read_tool])

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    system_message = SystemMessage(content=instructions)
    
    agent_executor = create_react_agent(llm, tools, prompt=system_message)
    log.info(f"Agent '{agent_type}' created successfully for session '{session_id}'.")
    
    return agent_executor