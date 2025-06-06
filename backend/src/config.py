import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")