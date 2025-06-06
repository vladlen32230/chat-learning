import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
DEEPINFRA_API_KEY = os.environ["DEEPINFRA_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]