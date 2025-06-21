import os
import threading
import pyaudio
import wave
from dotenv import load_dotenv
from google.cloud import speech
from google.cloud import texttospeech
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./google_credentials.json"

if not GOOGLE_API_KEY or not GOOGLE_CLOUD_CREDENTIALS:
    raise EnvironmentError("Set GOOGLE_API_KEY and GOOGLE_APPLICATION_CREDENTIALS in your .env file")

# Set up Gemini
genai.configure(api_key=GOOGLE_API_KEY)


class AIAssistant:
    def __init__(self):
        self.speech_client = speech.SpeechClient()
        self.tts_client = texttospeech.TextToSpeechClient()
        self.stop_stream_flag = threading.Event()
        self.audio_stream = None

        self.model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro",
            system_instruction="""
            You are a friendly, helpful tutor who teaches using the Feynman Technique.
            Explain topics simply, ask the student to explain back, then provide corrections
            or further clarification as needed.
            """
        )
        self.chat = self.model.start_chat()

    def speak(self, text, output_path="output.mp3"):
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        os.system(f"start {output_path}" if os.name == "nt" else f"afplay {output_path}")  # Cross-platform playback

    def generate_ai_response(self, transcript):
        print(f"\n You: {transcript}")
        response = self.chat.send_message(transcript)
        print(f"\n Tutor: {response.text}")
        self.speak(response.text)  # speak() will finish before next step
        self.start_transcription()  # Now start listening again

    def start_transcription(self):
        def audio_stream_generator():
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            self.audio_stream = stream
            try:
                while not self.stop_stream_flag.is_set():
                    yield stream.read(1024, exception_on_overflow=False)
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()

        def recognize_stream():
            requests = (
                speech.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in audio_stream_generator()
            )

            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US"
                ),
                interim_results=True
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
                        print(f"Transcribed: {transcript}")
                        if result.is_final:
                            self.generate_ai_response(transcript)

        threading.Thread(target=recognize_stream).start()

    def stop_transcription(self):
        self.stop_stream_flag.set()
        if self.audio_stream:
            self.audio_stream.close()


# Run the assistant
if __name__ == "__main__":
    assistant = AIAssistant()
    greeting = (
        "Hello! I'm your Learning Assistant. "
        "We'll be using the Feynman technique today. I'll explain topics simply, "
        "and you'll teach them back to me. Let's begin! What would you like to learn?"
    )
    assistant.speak(greeting)
    assistant.start_transcription()
    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nStopping transcription...")
        assistant.stop_transcription()
        print("Goodbye!")