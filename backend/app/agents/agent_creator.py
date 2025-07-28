import logging
from typing import List
from langchain.agents import AgentExecutor
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage

from app.llm import get_llm
# Import all our tools
from app.tools import ReadFileTool, get_retriever_tool, ListFilesTool

log = logging.getLogger(__name__)

def create_agent(session_id: str, agent_type: str) -> AgentExecutor:
    """
    Factory function to create a specific type of ReAct agent.
    """
    log.info(f"Creating agent of type '{agent_type}' for session '{session_id}'")
    llm = get_llm()
    tools: List[BaseTool] = []
    instructions = ""

    # Common tools for exploration
    list_tool = ListFilesTool(session_id=session_id)
    read_tool = ReadFileTool(session_id=session_id)

    if agent_type == "QA_Agent":
        instructions = (
            "You are a Q&A expert. Your goal is to answer questions about the codebase. "
            "First, use the 'list_files' tool to understand the codebase structure. "
            "Then, use the 'codebase_retriever' tool to find relevant code snippets and answer the user's question."
        )
        tools.extend([list_tool, get_retriever_tool(session_id)])

    elif agent_type == "Debug_Agent":
        instructions = (
            "You are a debugging expert. The user will ask you to find bugs in a specific file. "
            "If you are unsure of the exact file path, use the 'list_files' tool to find it. "
            "Then, use the 'read_file' tool to get the file's content. "
            "Finally, analyze it for bugs, vulnerabilities, and errors, and provide a detailed report."
        )
        tools.extend([list_tool, read_tool])

    elif agent_type == "Refactor_Agent":
        instructions = (
            "You are a code refactoring specialist. The user will ask you to improve a file. "
            "If you are unsure of the exact file path, use the 'list_files' tool to find it. "
            "Then, use the 'read_file' tool to get the file's content. "
            "Rewrite and improve the code, focusing on readability, efficiency, and best practices. Explain the key changes you made."
        )
        tools.extend([list_tool, read_tool])
    
    elif agent_type == "Diagram_Agent":
        instructions = (
            "You are a software architecture visualizer. "
            "If the user wants to diagram a specific file or logic, use 'list_files' to find the path, then 'read_file' to understand its contents. "
            "Generate a diagram in Mermaid.js syntax that accurately represents the architecture or logic flow. ONLY output the Mermaid.js code block."
        )
        tools.extend([list_tool, read_tool])

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    system_message = SystemMessage(content=instructions)
    
    agent_executor = create_react_agent(llm, tools, prompt=system_message)
    log.info(f"Agent '{agent_type}' created successfully for session '{session_id}'.")
    
    return agent_executor