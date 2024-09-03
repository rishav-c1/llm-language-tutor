from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import speech_v2
from google.oauth2 import service_account
from google.api_core import exceptions as google_exceptions
import anthropic
import asyncio
import io
import base64
from gtts import gTTS
from langdetect import detect, LangDetectException
from pydub import AudioSegment
import re
from num2words import num2words
import os
from dotenv import load_dotenv
import requests
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
app = FastAPI()


PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sunny-atrium-388515")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(credentials_path)
speech_client = speech_v2.SpeechClient(credentials=credentials)
# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class PromptRequest(BaseModel):
    prompt: str
    context: str = ""
    is_new_chat: bool = False

class FeedbackRequest(BaseModel):
    context: str

def tts(text, lang):
    return gTTS(text=text, lang=lang, tld="com")

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return None

def preprocess_text(text):
    text = text.replace("/", " out of ")
    text = re.sub(r'\b\d+\b', lambda m: num2words(int(m.group())), text)
    return text

def split_into_chunks(words, chunk_size=20):
    return [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]

def generate_multilingual_audio(text):
    segments = []
    preprocessed_text = preprocess_text(text)
    words = re.findall(r"\S+\s*", preprocessed_text)
    chunks = split_into_chunks(words)

    for chunk in chunks:
        chunk_text = ''.join(chunk).strip()
        curr_lang = detect_language(chunk_text)
        if curr_lang not in ['en', 'es']:
            curr_lang = 'en'
        audio = tts(chunk_text, curr_lang)
        with io.BytesIO() as f:
            audio.write_to_fp(f)
            f.seek(0)
            segment = AudioSegment.from_mp3(f)
            segments.append(segment)

    combined = sum(segments)
    buffer = io.BytesIO()
    combined.export(buffer, format="mp3")
    return buffer.getvalue()

@app.post("/api/learn")
async def learn(prompt_request: PromptRequest):
    context = "" if prompt_request.is_new_chat else prompt_request.context
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Context: {context}\n\n{prompt_request.prompt}"
                }
            ]
        }
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=100,
        temperature=0.01,
        system="You are a Spanish teacher. Teach me 20 basic Spanish words through conversation. Score my responses (1-5). Use format: Español sentence (English translation); Begin simple.",
        messages=messages
    )

    text_response = response.content[0].text
    audio = generate_multilingual_audio(text_response)
    audio_b64 = base64.b64encode(audio).decode('utf-8')

    return JSONResponse(content={"response": text_response, "audio": audio_b64})

@app.post("/api/feedback")
async def feedback(feedback_request: FeedbackRequest):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Here's the context of a Spanish learning conversation:\n\n{feedback_request.context}\n\nBased on this conversation, please provide:\n1. Español words learned\n2. Overall evaluation score (1-5) of the learner's progress\n3. Very short constructive feedback and suggestions for improvement"
                }
            ]
        }
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=150,
        temperature=0,
        system="You are an AI language learning assistant tasked with providing feedback and evaluation for Spanish learners.",
        messages=messages
    )

    return JSONResponse(content={"feedback": response.content[0].text})

@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    print("Starting speech_to_text function")
    try:
        content = await audio.read()
        print(f"Received audio file, size: {len(content)} bytes")

        print("Configuring recognition...")
        config = speech_v2.RecognitionConfig(
            auto_decoding_config=speech_v2.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="long",
        )

        print("Creating recognition request...")
        request = speech_v2.RecognizeRequest(
            recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
            config=config,
            content=content,
        )

        print("Sending request to Google Speech-to-Text API")
        response = speech_client.recognize(request=request)
        print("Received response from Google Speech-to-Text API")

        print("Processing API response...")
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript

        print(f"Transcription result: {transcript}")

        return JSONResponse(content={"transcript": transcript})

    except Exception as e:
        print(f"Error in speech_to_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)