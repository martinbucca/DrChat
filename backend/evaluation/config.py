import os
from dotenv import load_dotenv
load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "storage")

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

FILE_SERVICE_BASE_URL= os.environ.get('FILE_SERVICE_BASE_URL')
REGISTER_URL= os.environ.get('REGISTER_URL')
SESSION_URL= os.environ.get('SESSION_URL')
ANSWER_QUESTION= os.environ.get('ANSWER_QUESTION')

LLM_CHAT_MODEL = os.getenv('LLM_CHAT_MODEL')

GROQ_API_BASE = os.getenv('GROQ_API_BASE')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# To use ChatOpenAI from Groq, set the OPENAI_API_KEY environment variable to your Groq API key
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
