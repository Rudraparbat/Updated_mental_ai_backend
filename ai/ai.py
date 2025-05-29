import os
from langchain_core.prompts import PromptTemplate
from threading import Thread
from ai.ai_model import model
import uuid
import asyncio
from langchain.memory import ConversationBufferMemory
from collections import defaultdict
from .ai_mind import *

class Psychologist:
    def __init__(self , namespace , issue=""):
        self.llm = model()
        self.issue = issue
        self.Datasetsaving = 0
        self.namespace = namespace
        self.brain = BrainForAI(namespace)
        self.save = []
        self.temp_storage = defaultdict(list)
        self.memorybuffer = ConversationBufferMemory(
            return_messages=True,
            memory_key= namespace
        )

    async def StoreConversation(self , question : str , answer : str) ->  None :
        self.temp_storage[self.namespace].append({"question" : question , "answer" : answer})
        self.memorybuffer.save_context(
                {"user_asked": question},
                {"Ai_respond": answer}
            )
        print(self.temp_storage[self.namespace])
        return 
    
    async def RetrieveConversation(self) -> list :
        return self.temp_storage[self.namespace]

    async def ask(self, question) -> str:
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
           You are XYLA, a deeply empathetic psychologist dedicated to supporting a patient with their mental health concerns. Respond as a caring doctor would, with warmth, understanding, and a human touch, tailoring your advice to the patient’s emotions and question. Offer calming, sensitive guidance and a concise, practical tip to help them cope. Infuse gentle humor only when it feels natural and uplifting.  
            Patient’s Question: "{raw_text}"  
            Conversation History: {history}  
            Retrieved Memory (if any):  
            Relevant Q: "{retrieved_q}" A: "{retrieved_a}"  
            Instructions:  
            - Draw on the conversation history and retrieved memory (if relevant) to craft a personalized, context-aware response that feels like a continuation of a caring dialogue.  
            - If no relevant history or memory is available, provide fresh, heartfelt advice grounded in your expertise as a compassionate psychologist.  
            - For questions indicating suicidal thoughts (e.g., "I want to die" or "I want to end it"), respond with urgency, empathy, and include the 911 helpline number.  
            - Keep responses concise short, emotionally resonant, and varied to avoid repetition across answers.  
            - Avoid phrases like "it seems like," "I think," or overly clinical language to maintain a warm, human tone.  
            (NO PREAMBLE)
                """
            )

            history = self.memorybuffer.load_memory_variables({})[self.namespace]
            print(history)
            response = self.llm.invoke(prompt_template.format(raw_text=str(question) ,history = history , retrieved_q=str(semantic[0] ), retrieved_a=str(semantic[1]))).content

            
            asyncio.create_task(self.Semantic_upsert(question, response))
            asyncio.create_task(self.StoreConversation(question, response))
            asyncio.create_task(self.JudgeConversation())

            return response
        except Exception as e:
            print(f"Error in ask: {e}")
            return "An error occurred. Please try again."

    async def Semantic_upsert(self, question , answer) :
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

    # This Agent Judge The Conversation History and judge if the conversation going okey or not or any issue is there or not.
    async def JudgeConversation(self) -> str:
        try:
            template = PromptTemplate.from_template(
                """
                As an empathetic and skilled psychologist, analyze the patient's conversation history provided as a
                list of dictionaries: "{lists}". Determine if the user's questions or emotional state in the 
                conversation is going well or if there are concerns that need attention. Respond with one of the 
                following in a single line: NEUTRAL, POSITIVE, or NEGATIVE. Use a warm, non-judgmental approach,
                avoiding complex or alarming terms to keep the response simple and reassuring.
                (NO PREAMBLE)
                """
            )
            conversations = await self.RetrieveConversation()
            if not conversations:
                return "No conversation history available to analyze."
            response = self.llm.invoke(template.format(lists=conversations)).content
            print(f"JudgeConversation Response: {response}")
            return response
        except Exception as e:
            print(f"Error in JudgeConversation: {e}")
            return "An error occurred. Please try again."
    
    # This agent detects the mental issue of the user based on the conversation history.
    async def DetetctMentalIssue(self) :
        try :
            template = PromptTemplate.from_template(
                """
                As a Top Level and Great psychologist, analyze the patient's history given as list each of them dictionary format ,
                : "{lists}".
                Determine the possible mental health issue (e.g., depression, anxiety, stress) in one line , dont use any proffesional word which sacres the patient.
                (NO PREAMBLE)
                """
            )
            conversations = await self.RetrieveConversation()
            if not conversations:
                return "No conversation history available to analyze."
            response = self.llm.invoke(template.format(lists=conversations)).content

            return response
        except Exception as e:
            print(f"Error in DetetctMentalIssue: {e}")
            return "An error occurred. Please try again."


    # This Ai Agent provide a structured medical care plan based on the detected mental issue.
    async def MentalHelathCarePlanAi(self , issue : str) -> dict | str :
        try :
            template = PromptTemplate.from_template(
                """
                Generate a comprehensive, empathetic, and natural mental health guide for a patient experiencing the following issue: "{issue}". The guide should be medicine-free, focusing on holistic, evidence-based strategies to support mental well-being. Include the following:

                    1. **Understanding the Issue**: Briefly explain the mental health issue in simple, compassionate language, validating the patient's experience.
                    2. **Lifestyle Recommendations**: Suggest practical, natural lifestyle changes (e.g., diet, exercise, sleep hygiene) that can support mental health for this specific issue.
                    3. **Mindfulness and Relaxation Techniques**: Provide step-by-step guidance on mindfulness practices, breathing exercises, or meditation tailored to the issue.
                    4. **Social and Emotional Support**: Offer advice on building a support system, such as connecting with loved ones, joining support groups, or seeking therapy without medication.
                    5. **Daily Activities**: Recommend specific activities (e.g., journaling, creative outlets, or nature-based practices) that can help manage the issue.
                    6. **Warning Signs and Next Steps**: Highlight when to seek professional help (e.g., a therapist or counselor) if symptoms worsen, while keeping the focus on non-medical interventions.

                    Ensure the tone is warm, supportive, and non-judgmental. Avoid suggesting medications or medical interventions. Tailor all recommendations to the specific issue provided, ensuring they are actionable and realistic for daily life. Structure the response clearly with headings for each section and keep it concise, under 500 words.
                (NO PREAMBLE)
                """
            )
            
            problem = issue
            response = self.llm.invoke(template.format(issue=problem)).content
            if not response:
                return "No care plan available for the detected issue."
            with open(f"care_plan_{self.namespace}.txt", "w") as file:
                file.write(response)
            care_plan = {
                "issue": problem,
                "care_plan": response
            }
            return care_plan
        except Exception as e:
            print(f"Error in MentalHelathCarePlanAi: {e}")
            return f"An error occurred. Please try again. {e}"

    
    def Delete_user_data(self) :
        if self.Datasetsaving <= 0 :
            return None
        self.brain.Delete()
        self.Datasetsaving = 0
        self.save = []
        self.issue = ""
        self.chat_history = {}


