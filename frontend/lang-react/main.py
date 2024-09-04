from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import speech_v2
from google.oauth2 import service_account
import anthropic
import io
import base64
from gtts import gTTS
from langdetect import detect, LangDetectException
from pydub import AudioSegment
import re
from num2words import num2words
import os
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import asyncio
from collections import defaultdict


message_count = defaultdict(int)

load_dotenv()
app = FastAPI()
cache = {}


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
    if not text.strip():
        return None  # Return None for empty strings
    return gTTS(text=text, lang=lang, tld="com")

def detect_language(text):
    if not text.strip():
        return 'en'  # Default to English for empty strings
    try:
        return detect(text)
    except LangDetectException:
        return 'en'  # Default to English if detection fails

def preprocess_text(text):
    # Add spaces around punctuation marks
    text = re.sub(r'([¿¡?!])', r' \1 ', text)
    text = re.sub(r'(\d+/\d+)(\s)', r'\1,\2', text)
    
    # Split text into sentences and filter out empty ones
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    processed_sentences = []
    for sentence in sentences:
        lang = detect_language(sentence)
        processed_sentences.append((sentence, lang))
    
    return processed_sentences

def generate_multilingual_audio(text):
    segments = []
    preprocessed_sentences = preprocess_text(text)

    for sentence, lang in preprocessed_sentences:
        audio = tts(sentence, lang)
        if audio:  # Only process if audio is not None
            with io.BytesIO() as f:
                audio.write_to_fp(f)
                f.seek(0)
                segment = AudioSegment.from_mp3(f)
                segments.append(segment)

    if not segments:
        return None  # Return None if no audio was generated

    combined = sum(segments)
    buffer = io.BytesIO()
    combined.export(buffer, format="mp3")
    return buffer.getvalue()

@app.post("/api/learn")
async def learn(prompt_request: PromptRequest):
    global message_count
    
    # Increment message count for this session
    session_id = 123  # TODO: to add this to PromptRequest model
    message_count[session_id] += 1

    context = "" if prompt_request.is_new_chat else prompt_request.context
    
    cached_summary = cache.get(f'summary_{session_id}', '')
    if cached_summary and not prompt_request.is_new_chat:
        context = f"Previous lesson summary:\n{cached_summary}\n\nContinuation:\n{context}"
    
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
        max_tokens=150,
        temperature=0.1,
        system="""
        You are a helpful Spanish teacher. Teach basic Spanish words through conversation and keep your messages short, simple and cohesive and at times test the user on learnt words.
        Score the responses (1-5) honestly with good reasoning. Use format: English instruction with the Spanish phrase. Begin simple.""",
        messages=messages
    )


    text_response = clean_response(response.content[0].text)
    audio = generate_multilingual_audio(text_response)
    audio_b64 = base64.b64encode(audio).decode('utf-8')
    
    if message_count[session_id] % 10 == 0:
        print(f"Caching conversation summary for session {session_id}")
        await cache_conversation_summary(session_id, context + "\n" + text_response)

    return JSONResponse(content={"response": text_response, "audio": audio_b64})

def clean_response(text_response):
    text_response = text_response.rstrip()
    
    if not text_response:
        return text_response
    valid_endings = set('.!?:;"\')]')

    if text_response[-1] not in valid_endings:
        last_newline = text_response.rfind('\n')
        if last_newline != -1:
            text_response = text_response[:last_newline]
        else:
            text_response = ""

    return text_response

async def cache_conversation_summary(session_id: str, context: str):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Please provide a summary of this Spanish learning conversation:\n\n{context}"
                }
            ]
        }
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=200,
        temperature=0,
        system="You are an AI language learning assistant tasked with summarizing Spanish learning conversations.",
        messages=messages
    )

    summary = response.content[0].text
    cache[f'summary_{session_id}'] = summary

@app.post("/api/feedback")
async def feedback(feedback_request: FeedbackRequest):
    feedback_prompt = """
    As an AI language learning assistant, analyze the following Spanish learning conversation and provide a comprehensive lesson summary. Include:

    1. Spanish words and phrases learned (list up to 10)
    2. Topics covered
    3. Grammar points discussed
    4. Exercises or activities completed
    5. Areas for improvement
    6. Overall evaluation score (1-5) of the learner's progress
    7. Constructive feedback
    8. Suggested next steps for the learner

    Present the summary in a clear, structured format.

    Conversation context:
    {context}

    Lesson Summary:
    """

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": feedback_prompt.format(context=feedback_request.context)
                }
            ]
        }
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=500,
        temperature=0,
        system="You are an AI language learning assistant tasked with providing comprehensive feedback and evaluation for Spanish learners.",
        messages=messages
    )

    lesson_summary = response.content[0].text

    # Cache the lesson summary for use in the next /learn call
    cache['latest_summary'] = lesson_summary

    return JSONResponse(content={"feedback": lesson_summary})

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