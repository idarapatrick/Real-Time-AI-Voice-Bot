import assemblyai as aai
from openai import OpenAI
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv


"""
The steps indicated before the first class are for testing locally to ensure that the API keys are available and that they work properly.

First Step: load OpenAI, AssemblyAI, and Elevenlabs API keys when testing locally.
- Note: you have to have saved your API keys in a .env file for this to work
"""


load_dotenv(dotenv_path="API-Keys.env") #chnage the file path and add the path to the .env file that contains your API keys

#Fetch keys from environemnt variables
ASSEMBLYAI_KEY = os.getenv("ASSEMBLYAI_KEY")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY")

if not all([ASSEMBLYAI_KEY, OPENAI_KEY, ELEVENLABS_KEY]):
    raise EnvironmentError("One or more API keys are missing! Load from your environment variables or create and add the API keys to a .env file")

class AI_Assistant:
    def __init__(self):
        #set the API keys
        aai.settings.api_key = ASSEMBLYAI_KEY
        self.openai_client = OpenAI(api_key = OPENAI_KEY)
        self.elevenlabs_api_key = ELEVENLABS_KEY
        
        self.elevenlabs_api_key = ElevenLabs(api_key= self.elevenlabs_api_key)
        self.transcriber = None
        
        #set the initial prompt
        self.interaction = [{"role":"system", "content":"""You are a narrator. You have people coming to you to ask for poetic stories where you narrate like an expert poet. Sound narrative and poetic.
                             """}]
        
        
    def generate_audio(self, text):
        self.interaction.append({"role":"assistant", "content": text})
        print(f"\n AI Guide: {text}")
            
        audio_stream = self.elevenlabs_client.generate(text = text, voice = "Brian", stream = True)
            
        stream(audio_stream)
        
    def generate_ai_response(self, transcript): # accepts the current 
        self.stop_transciption()
        self.interaction.append("role":"user", "content": transcript.text)
        print(f"\n User: {transcript.text}", end ="\n")
        
        # generate response with OpenAI
        response = self.openai_client.chat.completions.create(
            model = "get-4o-mini"
            messages= self.interaction
        )
        
        

        
