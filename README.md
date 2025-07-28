# 🚀 Codebase Copilot

**Codebase Copilot** is a LangGraph-powered multi-agent application designed to help users understand, debug, and interact with large codebases using LLMs. It offers intelligent assistance for codebase Q&A, summaries, file-by-file reasoning, and flowchart generation using a modular multi-LLM backend and a Streamlit UI.

---

## 🌐 Features

- 🔍 **Repo Q&A Assistant** – Ask questions about the whole repository or a single file.
- 🧠 **Summarization Agent** – Get summaries of code files or directories.
- 🛠️ **Debugging Agent** – Help debug issues or reason through errors.
- 🧮 **Web Search & Math Agent** – Optional web search or math tool when required.
- 🖼️ **Flowchart Generator** – Visualize the logic/structure of code in flowcharts.
- 📂 **Multiple Input Modes** – Upload local zip, fetch GitHub repo, or use Drive.
- 🧬 **Multi-LLM Support** – Switch between OpenAI, Gemini, DeepSeek, Anthropic, Groq.
- 💾 **Session Memory** – Each session stores vector DB and agent memory separately.

---

## 📁 Project Structure

```

codebase-copilot/
├── backend/
│   ├── app/
│   │   ├── agents/         # LangGraph agents: Q\&A, Summarizer, Debugger, etc.
│   │   ├── llm/            # LLM client wrappers (OpenAI, Groq, etc.)
│   │   ├── routes/         # FastAPI route definitions
│   │   ├── tools/          # Utility tools like WebSearch, MathTool
│   │   └── utils/          # Helper functions
│   ├── langgraph\_graph.py  # LangGraph graph and workflow logic
│   └── requirements.txt    # Backend dependencies
├── frontend/
│   ├── streamlit\_app.py    # Frontend Streamlit app
│   └── requirements.txt    # Frontend dependencies
├── sessions/               # Per-session vector DB / memory storage
├── .env                    # Environment variables (API keys)
└── README.md               # This file

````

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/sumitcoder01/Codebase-Copilot.git
cd Codebase-Copilot
````

### 2. Add Environment Variables

Fill in the `.env` file:

```env
LLM_PROVIDER=DEEPSEEK

DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
```

### 3. Install Dependencies

### create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
```

#### Frontend

```bash
cd ../frontend
pip install -r requirements.txt
```

---

## 🚀 Run the App

### 1. Start FastAPI Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Start Streamlit Frontend

In a new terminal:

```bash
cd frontend
streamlit run streamlit_app.py
```

---

## 📌 Tech Stack

* **LangGraph**, **LangChain**, **FastAPI**, **Streamlit**
* **LLM Providers**: OpenAI, Gemini, DeepSeek, Anthropic, Groq
* **Vector Store**: ChromaDB
* **Session Memory**: File-based isolation in `sessions/`

---

## 🧠 Future Enhancements

* Support for docstring generation
* Deeper GitHub integration with PR assistance
* Multi-repo chat sessions
* LangSmith instrumentation for agent tracing

---

## 🙌 Contributions

Contributions are welcome! Feel free to open issues or submit PRs.