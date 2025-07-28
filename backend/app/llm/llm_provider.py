import os
import logging
from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

load_dotenv()
log = logging.getLogger(__name__)

def get_llm():
    """
    Reads the environment variables and returns the configured LLM provider instance.
    """
    provider = os.getenv("LLM_PROVIDER")
    log.info(f"Attempting to initialize LLM provider: {provider}")

    if not provider:
        log.error("LLM_PROVIDER environment variable not set.")
        raise ValueError("LLM_PROVIDER environment variable is not set.")

    provider = provider.upper()

    if provider == "DEEPSEEK":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set in the environment.")
        return ChatDeepSeek(api_key=api_key, model="deepseek-chat" , temperature=0.7)

    elif provider == "GEMINI":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the environment.")
        return ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)

    elif provider == "OPENAI":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        return ChatOpenAI(api_key=api_key, model="gpt-4-turbo")

    elif provider == "ANTHROPIC":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in the environment.")
        return ChatAnthropic(api_key=api_key, model="claude-3-sonnet-20240229")
        
    elif provider == "GROQ":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment.")
        return ChatGroq(api_key=api_key, model_name="llama3-8b-8192")

    else:
        log.error(f"Unsupported LLM provider: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}")