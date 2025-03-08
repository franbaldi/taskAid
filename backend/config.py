# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

MONGO_URI = os.getenv("MONGO_URI")
OLLAMA_URL = os.getenv("OLLAMA_URL")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
PORT = int(os.getenv("PORT"))
DEFAULT_LLM_MODEL = "llama2"  # Change this to a model you know is installed

# Optional: Define a list of fallback models to try if the default isn't available
FALLBACK_LLM_MODELS = ["llama3", "mistral", "gemma", "phi"]