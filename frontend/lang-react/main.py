from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
import io
import base64
from gtts import gTTS
from langdetect import detect, LangDetectException
from pydub import AudioSegment
import re
from num2words import num2words

app = FastAPI()

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key="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")

app.mount("/static", StaticFiles(directory="build/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

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
        curr_lang = detect_language(chunk_text) or 'en'
        
        audio = tts(chunk_text, curr_lang)
        with io.BytesIO() as f:
            audio.write_to_fp(f)
            f.seek(0)
            segment = AudioSegment.from_mp3(f)
            segments.append(segment)
        
        # segments.append(AudioSegment.silent(duration=500))

    combined = sum(segments)
    buffer = io.BytesIO()
    combined.export(buffer, format="mp3")
    return buffer.getvalue()

@app.get("/")
async def read_root():
    return FileResponse('../frontend/build/index.html')

@app.get("/{catch_all:path}")
async def catch_all(request: Request):
    return FileResponse('../frontend/build/index.html')

@app.post("/learn")
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
        system="You're a Spanish teacher. Teach me 20 basic Spanish words through conversation. Start simple. Score my responses (1-5). Use format: Spanish phrase (English translation). Begin.",
        messages=messages
    )

    text_response = response.content[0].text
    audio = generate_multilingual_audio(text_response)
    audio_b64 = base64.b64encode(audio).decode('utf-8')

    return {"response": text_response, "audio": audio_b64}

@app.post("/feedback")
async def feedback(feedback_request: FeedbackRequest):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Here's the context of a Spanish learning conversation:\n\n{feedback_request.context}\n\nBased on this conversation, please provide:\n1. Spanish words learned\n2. Overall evaluation score (1-5) of the learner's progress\n3. Very short constructive feedback and suggestions for improvement"
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

    return {"feedback": response.content[0].text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)