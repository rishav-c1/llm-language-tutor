import torch
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import base64
import numpy as np
from scipy import signal
import json

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load a smaller model for faster processing
model_name = "facebook/wav2vec2-base-960h"
processor = Wav2Vec2Processor.from_pretrained(model_name)
model = Wav2Vec2ForCTC.from_pretrained(model_name)

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def reduce_noise(audio_chunk, noise_reduce_factor=0.9):
    return signal.wiener(audio_chunk, noise_reduce_factor)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            audio_data = base64.b64decode(data['audio'])
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Apply noise reduction
            audio_array = reduce_noise(audio_array)
            
            # Process audio data
            with torch.no_grad():
                input_values = processor(audio_array, return_tensors="pt", sampling_rate=16000).input_values
                input_values = input_values.to(device)
                logits = model(input_values).logits
                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = processor.decode(predicted_ids[0])
            
            await websocket.send_json({"transcription": transcription})
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        await websocket.close()

@app.get("/")
async def root():
    return {"message": "Speech Recognition Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)