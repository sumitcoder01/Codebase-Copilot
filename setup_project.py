import os

# --- Project Structure Definition ---

# Define the root directory name
ROOT_DIR = ""

# Define all directories to be created
# Using os.path.join to ensure cross-platform compatibility
DIRS = [
    os.path.join(ROOT_DIR, "backend"),
    os.path.join(ROOT_DIR, "backend", "app"),
    os.path.join(ROOT_DIR, "backend", "app", "agents"),
    os.path.join(ROOT_DIR, "backend", "app", "llm"),
    os.path.join(ROOT_DIR, "backend", "app", "routes"),
    os.path.join(ROOT_DIR, "backend", "app", "tools"),
    os.path.join(ROOT_DIR, "backend", "app", "utils"),
    os.path.join(ROOT_DIR, "frontend"),
    os.path.join(ROOT_DIR, "sessions"), # For storing session-specific data like vector dbs
]

# Define all empty files to be created
# We include __init__.py files to make directories Python packages
FILES = {
    # Backend files
    os.path.join(ROOT_DIR, "backend", "langgraph_graph.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "main.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "agents", "__init__.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "llm", "__init__.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "routes", "__init__.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "tools", "__init__.py"): "",
    os.path.join(ROOT_DIR, "backend", "app", "utils", "__init__.py"): "",
    
    # Frontend files
    os.path.join(ROOT_DIR, "frontend", "streamlit_app.py"): "",
    os.path.join(ROOT_DIR, "frontend", "requirements.txt"): "streamlit\nrequests",
    
    # Root files
    os.path.join(ROOT_DIR, ".env"): (
        "# --- LLM Provider & API Keys ---\n"
        "# Set the provider to one of: DEEPSEEK, GEMINI, OPENAI, ANTHROPIC, GROQ\n"
        "LLM_PROVIDER=DEEPSEEK\n\n"
        "# Fill in the API keys for the providers you intend to use\n"
        "DEEPSEEK_API_KEY=\"YOUR_DEEPSEEK_API_KEY\"\n"
        "GOOGLE_API_KEY=\"YOUR_GEMINI_API_KEY\"\n"
        "OPENAI_API_KEY=\"YOUR_OPENAI_API_KEY\"\n"
        "ANTHROPIC_API_KEY=\"YOUR_ANTHROPIC_API_KEY\"\n"
        "GROQ_API_KEY=\"YOUR_GROQ_API_KEY\"\n"
    ),
    os.path.join(ROOT_DIR, "README.md"): "# Codebase Copilot",
}

# --- Script Execution ---

def setup_project_structure():
    """Creates the directories and files for the project."""
    print("--- Starting Project Setup ---")

    # Create sub-directories
    for dir_path in DIRS:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Successfully created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")

    # Create empty files with optional content
    for file_path, content in FILES.items():
        try:
            with open(file_path, 'w') as f:
                if content:
                    f.write(content)
            print(f"Successfully created file: {file_path}")
        except IOError as e:
            print(f"Error creating file {file_path}: {e}")
    
    # You already have the backend requirements.txt from the previous step,
    # but we can create it here if it doesn't exist for completeness.
    backend_req_path = os.path.join(ROOT_DIR, "backend", "requirements.txt")
    if not os.path.exists(backend_req_path):
        with open(backend_req_path, 'w') as f:
             f.write((
                "fastapi\n"
                "uvicorn[standard]\n"
                "python-dotenv\n"
                "python-multipart\n"
                "langchain\n"
                "langgraph\n"
                "langchain-core\n"
                "chromadb\n"
                "tiktoken\n"
                "langchain-deepseek\n"
                "langchain-google-genai\n"
                "langchain-openai\n"
                "langchain-anthropic\n"
                "langchain-groq\n"
            ))
        print(f"Created file: {backend_req_path}")


    print("--- Project Setup Complete ---")
    print(f"\nNext steps:")
    print(f"1. cd {ROOT_DIR}")
    print("2. Fill in your API keys in the .env file.")
    print("3. Install dependencies for the backend and frontend.")

if __name__ == "__main__":
    setup_project_structure()