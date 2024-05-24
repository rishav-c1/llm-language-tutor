import subprocess
import whisper
import time


def transcribe_audio(audio_file_path):
    # Ensure ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg is not installed or not found in PATH.")

    # Load the model and time the loading process
    start_time = time.time()
    model = whisper.load_model("base")
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds")

    # Transcribe the audio file and time the transcription process
    start_time = time.time()
    result = model.transcribe(audio_file_path)
    transcription_time = time.time() - start_time
    print(f"Transcription completed in {transcription_time:.2f} seconds")

    # Print the transcript
    print("Transcript:", result)
    with open('transcript', 'w') as file:
        file.write(result['text'])


# Specify the audio file path
audio_file_path = r"C:\lang\audio recordings\harvard.wav"

# Time the entire transcription process
start_time = time.time()
transcribe_audio(audio_file_path)
total_time = time.time() - start_time
print(f"Total execution time: {total_time:.2f} seconds")

