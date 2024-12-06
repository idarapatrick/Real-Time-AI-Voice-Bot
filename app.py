from setup_google_credentials import setup_google_credentials
from openai import OpenAI
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from google.cloud import speech
import os
from dotenv import load_dotenv
import threading
import pyaudio

# Authenticate your Google credentials
setup_google_credentials()

load_dotenv()

# Fetch keys from environment variables
OPENAI_KEY = os.getenv("OPENAI_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY")

if not all([OPENAI_KEY, ELEVENLABS_KEY]):
    raise EnvironmentError("One or more API keys are missing! Load from your environment variables or create and add the API keys to a .env file")

class AI_Assistant:
    def __init__(self):
        # Initialize clients
        self.openai_client = OpenAI(api_key=OPENAI_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_KEY)
        self.speech_client = speech.SpeechClient()

        # Initialize variables
        self.interaction = [{"role": "system", "content": """You are a Learning Assistant. You have students coming to you to help them better understand certain topics. Use the Feynman technique to help them master. Remember to keep your response concise. Reject any topic that does not relate to the student learning something by returning this response 'sorry! I cannot help with that. Tell me a topic you would like to learn and I can help you understand it better'"""}]
        self.audio_stream = None
        self.stop_stream_flag = threading.Event()

    def generate_audio(self, text):
        self.interaction.append({"role": "assistant", "content": text})
        print(f"\nLearning Assistant: {text}")

        audio_stream = self.elevenlabs_client.generate(text=text, voice="Bill", stream=True)
        stream(audio_stream)

    def generate_ai_response(self, transcript_text):
        self.stop_transcription()
        self.interaction.append({"role": "user", "content": transcript_text})
        print(f"\nUser: {transcript_text}", end="\n")

        # Generate response with OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=self.interaction
        )

        self.generate_audio(response.choices[0].message.content)
        self.start_transcription()  # Let the user speak again
        print("\nReal-time transcription: ", end="\n")

    def start_transcription(self):
        def audio_stream_generator():
            """Streams microphone audio to the queue."""
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )
            self.audio_stream = stream

            try:
                while not self.stop_stream_flag.is_set():
                    data = stream.read(1024, exception_on_overflow=False)
                    yield data
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()

        def recognize_stream():
            """Handles the real-time transcription."""
            audio_generator = audio_stream_generator()
            for response in responses:
                if response.results:
                    result = response.results[0]
                    if result.alternatives:
                        transcript = result.alternatives[0].transcript
                        print(f"Transcribed Text: {transcript}")
            
                        # Process final transcriptions only
                        if result.is_final:
                            self.generate_ai_response(transcript)
                        requests = (
                            speech.StreamingRecognizeRequest(audio_content=chunk)
                            for chunk in audio_generator
                        )

            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                ),
                interim_results=True,
            )

            responses = self.speech_client.streaming_recognize(
                config=streaming_config,
                requests=requests
            )

            for response in responses:
                if response.results:
                    result = response.results[0]
                    if result.alternatives:
                        transcript = result.alternatives[0].transcript
                        print(f"Transcribed Text: {transcript}")
                        if result.is_final:
                            self.generate_ai_response(transcript)

        # Start recognition in a new thread
        transcription_thread = threading.Thread(target=recognize_stream)
        transcription_thread.start()

    def stop_transcription(self):
        self.stop_stream_flag.set()
        if self.audio_stream:
            self.audio_stream.close()


greeting = """Thank you for seeking my services today! I am your Learning Assistant. Pick a topic you would like to master and I will use the Feynman technique to make it easier for you to understand"""

ai_assistant = AI_Assistant()
ai_assistant.generate_audio(greeting)
ai_assistant.start_transcription()
