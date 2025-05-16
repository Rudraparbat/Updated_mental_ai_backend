from langchain_groq import ChatGroq
import os

def model() :
    api_key = os.getenv("API_KEY")
    try:
        llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        return llm
    except Exception as e:
        print(f"An error occurred: {e}")
        return False




