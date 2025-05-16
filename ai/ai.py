import os
from langchain_core.prompts import PromptTemplate
from threading import Thread
from ai.ai_model import model
import uuid

from .ai_mind import *

class Psychologist:
    def __init__(self , namespace , issue=""):
        self.llm = model()
        self.issue = issue
        self.Datasetsaving = 0
        # self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.brain = BrainForAI(namespace)
        self.save = []

    # def store_conversation(self, user_id, user_message, bot_response):
    #     """Store the conversation in a dictionary."""
    #     if user_id not in self.chat_history:
    #         self.chat_history[user_id] = []
    #     self.chat_history[user_id].append(f"User: {user_message}\nDoctor: {bot_response}")

    # def retrieve_history(self, user_id, num_messages=5):
    #     """Retrieve the last 'num_messages' conversation history for the user."""
    #     return "\n".join(self.chat_history.get(user_id, [])[-num_messages:])


    async def ask(self, question):
        """Process user input and return an AI-generated response."""
        if(self.Datasetsaving > 0) :
            semantic = self.brain.Search(question)
            if(semantic is  None) :
                semantic = ["", ""]
        else :
            semantic = ["", ""]
        
        
        try:
            prompt_template = PromptTemplate.from_template(
                """
            You are XYLA, a top-level psychologist here to help a patient who is suffering from mental issues, that you have to identify based on their question and emotion and have to give 
            Best Advice , EMOTIONAL SUPPORT and provide 'SHORT ADVICE' to the patient to overcome this issues and you have to be very 
            'calm' and 'patience' and 'SENSITIVE' in every situation  You have access to past question-answer pairs from the patient’s memory to inform your advice. 
            Patient’s Question: "{raw_text}"
            Retrieved Memory (if any):
            Relevant Q: "{retrieved_q}" A: "{retrieved_a}"
            (NO PREAMBLE)    
             Instructions:
             - Use the retrieved memory if it’s relevant to shape your advice naturally and show empathy.
             - If no memory is retrieved or it’s irrelevant, offer fresh advice based on your expertise ,cause you are the Top Psychologist.
             - If the Questions are like "i want to suicide" , "i want to die" or anything related to commiting death then provide 911 helpline number
             - Dont Use "it seems like" , "i think" , and also dont repeat same content in every answer.
            (NO PREAMBLE),(NOTE :- PROVIDE SHORT AND VALUABLE ANSWERS ON EVERY QUESTION try to crack jokes AND ANSWER THEM IN A RELAXING WAY)
            Just provide your best advice without explaining your thought process.
                """
            )

            response = self.llm.invoke(prompt_template.format(raw_text=str(question) , retrieved_q=str(semantic[0] ), retrieved_a=str(semantic[1]))).content

            Thread(target=self.Semantic_upsert , args=(question , response)).start()

            # Thread(target=self.detect_mental_issue, args=()).start()
            return response
        except Exception as e:
            print(f"Error in ask: {e}")
            return "An error occurred. Please try again."

    def Semantic_upsert(self, question , answer) :
        if(question == "" or answer == "") :
            return 
        self.save.append(
            {
                "id" : str(uuid.uuid4()),
                "question" : question,
                "answer" : answer,
            }
        )
        if(len(self.save) > 0) :
            self.brain.InsertData(self.save)
            self.Datasetsaving+=1
            self.save = []
        else :
            return 

    
    async def meditation_guide(self, issue):
        """Generate a guided meditation script based on the detected issue."""
        try:
            prompt_template = PromptTemplate.from_template(
                """
                As a psychologist named "Suri", provide a 5-minute guided meditation script to help with {raw_text}.
                Ensure it is structured, systematic, and includes timing for each step. provide it in txt file so user can download
                (NO PREAMBLE)
                """
            )
            return self.llm.invoke(prompt_template.format(raw_text=str(issue))).content
        except Exception as e:
            print(f"Error in meditation_guide: {e}")
            return "An error occurred while generating the meditation guide."

    def detect_mental_issue(self):
        """Analyze the conversation to detect possible mental health issues."""
        try:
            prompt_template = PromptTemplate.from_template(
                """
                As a psychologist, analyze the patient's history given as dictionary format : "{raw_text}".
                Determine the possible mental health issue (e.g., depression, anxiety, stress) in one line.
                (NO PREAMBLE)
                """
            )
            self.issue = self.llm.invoke(prompt_template.format(raw_text=self.chat_history)).content
        except Exception as e:
            print(f"Error in detect_mental_issue: {e}")

    
    def Delete_user_data(self) :
        if self.Datasetsaving <= 0 :
            return None
        self.brain.Delete()
        self.Datasetsaving = 0
        self.save = []
        self.issue = ""
        self.chat_history = {}


