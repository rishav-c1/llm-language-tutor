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


message_count = 0
load_dotenv()
app = FastAPI()
cache = []
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
    if lang not in ["es", "en"]:
        lang = "en"  # Default to English if language is not supported
    return gTTS(text=text, lang=lang, tld="com")

def detect_language(text):
    if not text.strip():
        return 'en'  
    try:
        return detect(text)
    except LangDetectException:
        return 'en'  

def preprocess_text(text):
    # Replace X/Y with "X out of Y"
    text = re.sub(r'(\d+)/(\d+)', lambda m: f"{m.group(1)} out of {m.group(2)}", text)
    
    # Convert standalone numbers to words
    def replace_number(match):
        num = int(match.group())
        return num2words(num, lang='es') if detect_language(match.group()) == 'es' else num2words(num)

    text = re.sub(r'\b\d+\b', replace_number, text)
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    processed_sentences = []
    for sentence in sentences:
        lang = detect_language(sentence)
        processed_sentences.append((sentence.strip(), lang))
    
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
    global cache
    
    # Increment message count for this session
    message_count += 1

    if prompt_request.is_new_chat:
        cache = []

    context = "" if prompt_request.is_new_chat else prompt_request.context
    if cache and not prompt_request.is_new_chat:
        cached_summary = cache.pop(0)
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
        You are a helpful Spanish teacher. Teach basics conversationally and score user (1-5) with reasoning. Keep responses short, simple, cohesive. Format: English instruction with Spanish phrase. Occasionally test learned words. Adapt difficulty. Start simple. Maintain conversation flow. Support bilingual content.""",
        messages=messages
    )


    text_response = clean_response(response.content[0].text)
    audio = generate_multilingual_audio(text_response)
    audio_b64 = base64.b64encode(audio).decode('utf-8')
    
    if message_count % 10 == 0:
        print(f"Caching conversation summary for session")
        await cache_conversation_summary(context + "\n" + text_response)

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

async def cache_conversation_summary(context: str):
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
        system="You are an AI language learning assistant tasked with summarizing Spanish learning conversations concisely while preserving as much information as possible.",
        messages=messages
    )

    summary = response.content[0].text
    cache.insert(0, summary)

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
    cache.insert(0, lesson_summary)

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
            language_codes=["es-US", "en-US"],
            model="latest_short",
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