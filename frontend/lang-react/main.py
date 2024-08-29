from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import anthropic

app = FastAPI()

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key="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")

# Serve static files from the current directory
app.mount("/src", StaticFiles(directory="."), name="src")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

class PromptRequest(BaseModel):
    prompt: str
    context: str = ""
    is_new_chat: bool = False

class FeedbackRequest(BaseModel):
    context: str

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

    return {"response": response.content[0].text}

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