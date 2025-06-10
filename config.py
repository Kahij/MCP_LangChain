import os
from dotenv import load_dotenv


load_dotenv()

#Access the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#Check if the API key is loaded properly 
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key not found. Make sure your .env file is configured correctly.")
