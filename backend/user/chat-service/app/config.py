import os
from dotenv import load_dotenv
load_dotenv()

VECTOR_INDEX_NAME = os.getenv('VECTOR_INDEX_NAME')

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

AZURE_OPENAI_API_KEY= os.environ.get('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION= os.environ.get('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_ENDPOINT= os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_EMBEDDINGS_MODEL= os.environ.get('AZURE_OPENAI_EMBEDDINGS_MODEL')

LLM_CHAT_MODEL = os.getenv('LLM_CHAT_MODEL')

GROQ_API_BASE = os.getenv('GROQ_API_BASE')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# To use ChatOpenAI from Groq, set the OPENAI_API_KEY environment variable to your Groq API key
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
