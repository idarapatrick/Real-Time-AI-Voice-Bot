import assemblyai as aai
from openai import OpenAI
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
import json
import websocket
import threading
import pyaudio


"""
The steps indicated before the first class are for testing locally to ensure that the API keys are available and that they work properly.

First Step: load OpenAI, AssemblyAI, and Elevenlabs API keys when testing locally.
- Note: you have to have saved your API keys in a .env file for this to work
"""


load_dotenv(dotenv_path="API-Keys.env") #chnage the file path and add the path to the .env file that contains your API keys

#Fetch keys from environemnt variables
WATSON_API_KEY = os.getenv("WATSON_API_KEY")
WATSON_URL = os.getenv("WATSON_URL")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY")

if not all([WATSON_API_KEY, WATSON_URL, OPENAI_KEY, ELEVENLABS_KEY]):
    raise EnvironmentError("One or more API keys are missing! Load from your environment variables or create and add the API keys to a .env file")

class AI_Assistant:
    def __init__(self):
        #set the API keys
        self.watson_api_key = WATSON_API_KEY
        self.watson_url = WATSON_URL
        self.instance_id = os.getenv("WATSON_INSTANCE_ID")
        self.watson_location = os.getenv("WATSON_LOCATION")
        self.openai_client = OpenAI(api_key = OPENAI_KEY)
        self.elevenlabs_client = ElevenLabs(api_key= ELEVENLABS_KEY)
        
        
        #set the initial prompt
        self.interaction = [{"role":"system", "content":"""You are a successful narrator. You have people coming to you to ask for poetic stories where you narrate like an expert poet. Sound narrative and poetic.
                             """}]
        
                
    def generate_audio(self, text):
        self.interaction.append({"role":"assistant", "content": text})
        print(f"\n AI Guide: {text}")
            
        audio_stream = self.elevenlabs_client.generate(text = text, voice = "Brian", stream = True)
            
        stream(audio_stream)
        
    def generate_ai_response(self, transcript_text): # accepts the current 
        self.stop_transciption()
        self.interaction.append({"role":"user", "content": transcript_text})
        print(f"\n User: {transcript_text}", end ="\n")
        
        # generate response with OpenAI
        response = self.openai_client.chat.completions.create(
            model = "gpt-4",
            messages= self.interaction
        )
        
        self.generate_audio(response.choices[0].messages.content)
        self.start_transcription() #Let the user speak again
        
        print(f"\nReal-time transcription: ", end = "\n")
        
        
    def start_transcription(self):
        def on_message(ws, message):
            response = json.loads(message)
            results = response.get("results", [{}])
            if results:
                transcript = results[0].get("alternatives", [{}])[0].get(transcript, "")
                print(f"Transcribed Text: {transcript}")
    
        def on_error(self, error):
            print(f"Transcription Error: {error}")
            
        def on_close(ws, close_status_code, code_msg):
            print("Websocket closed")        
            
        def on_open(ws):
            def stream_audio():
                # Initialize PyAudio
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16, 
                                channels = 1,
                                rate = 16000,
                                input = True,
                                frames_per_buffer = 1024)
                
                # Send a start message to Watson
                ws.send(json.dumps({
                    "action": "start",
                    "content-type": "audio/l16;rate=16000",
                    "interim_results": True
                }))
                print("Streaming audio...")
                
                try:
                    while True:
                        data = stream.read(1024, ezception_on_overflow = False)
                        ws.send(data, websocket.ABNF.OPCODE_BINARY)
                except KeyboardInterrupt:
                    print("Stopping the audio stream.")
                finally:
                    # Send stop signal
                    ws.send(json.dumps({"action": "stop"}))
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    
            threading.Thread(target=stream_audio).start()
        
        # Connecting to Watson WebSocket
        ws_url = f"wss://api.{self.watson_location}.speech-to-text.watson.cloud.ibm.com/instances/{self.instance_id}/v1/recognize?access_token={self.watson_api_key}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_message = on_message,
            on_error=on_error,
            on_close=on_close
        )
        websocket.enableTrace(True)
        ws.on_open = on_open
        ws.run_forever()
                
    
    def stop_transciption(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None    
            
            
greeting = """Thank you for seeking my services today! I am a poetic narrator. Kindly tell me what kind of story you need me to narrate"""

ai_assistant = AI_Assistant()
ai_assistant.generate_audio(greeting)
ai_assistant.start_transcription()        
            