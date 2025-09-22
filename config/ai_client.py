import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
def AIclient():
    client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    return client
