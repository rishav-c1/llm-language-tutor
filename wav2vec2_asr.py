import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import pyaudio
import numpy as np
from scipy import signal

model_name = "facebook/wav2vec2-base-960h"
processor = Wav2Vec2Processor.from_pretrained(model_name)
model = Wav2Vec2ForCTC.from_pretrained(model_name)

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Audio settings
RATE = 16000
CHUNK = 1024 * 10  # Larger chunk for better processing

# Initialize PyAudio
p = pyaudio.PyAudio()

# Simple noise reduction function
def reduce_noise(audio_chunk, noise_reduce_factor=0.9):
    return signal.wiener(audio_chunk, noise_reduce_factor)

def recognize_speech(audio):
    with torch.no_grad():
        input_values = processor(audio, return_tensors="pt", sampling_rate=RATE).input_values
        input_values = input_values.to(device)
        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.decode(predicted_ids[0])
    return transcription

def process_audio():
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening...")
    audio_buffer = np.zeros(RATE * 3)  # 3-second buffer
    try:
        while True:
            audio_chunk = np.frombuffer(stream.read(CHUNK), dtype=np.float32)
            audio_chunk = reduce_noise(audio_chunk)
            
            # Update buffer
            audio_buffer = np.roll(audio_buffer, -len(audio_chunk))
            audio_buffer[-len(audio_chunk):] = audio_chunk
            
            # Process if energy in the buffer is above a threshold
            if np.sqrt(np.mean(audio_buffer**2)) > 0.01:
                audio_tensor = torch.from_numpy(audio_buffer).float()
                transcription = recognize_speech(audio_tensor)
                print("Transcription:", transcription)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# Start processing audio
process_audio()