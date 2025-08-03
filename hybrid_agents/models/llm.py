from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
# llm = ChatOllama(
#     model="llama3.2-lora",
#     base_url="http://10.0.140.225:11434"  # IP máy host chạy Ollama
# )
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai", google_api_key="YOUR_API_KEY")
