import speech_recognition as sr

def listen_and_transcribe():
    """
    Listens to the microphone and returns the transcribed text.
    Returns an empty string if nothing was heard or an error occurred.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            # Calibrate briefly
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Listen for up to 10 seconds before giving up, and cut off after 30 seconds of speech
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
        # Call out to Google Web Speech API (Free, default limit applies)
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        print("Listening timed out.")
        return ""
    except sr.UnknownValueError:
        print("AI Google SpeechRecognition could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from AI Google SpeechRecognition service; {e}")
        return ""
    except Exception as e:
        print(f"Error during voice recognition: {e}")
        return ""

import threading

# Global Whisper Cache
whisper_model = None
whisper_lock = threading.Lock()

def _transcribe_whisper(audio_data):
    """Transcribes audio using a locally cached Whisper model for true offline usage."""
    global whisper_model
    try:
        import whisper
        import numpy as np
    except ImportError:
        print("Please install whisper: pip install -U openai-whisper setuptools-rust")
        return ""
        
    with whisper_lock:
        if whisper_model is None:
            print("Loading offline Whisper model (small.en)...")
            try:
                whisper_model = whisper.load_model("small.en")
            except Exception as e:
                print("\n[!] CRITICAL OFFLINE ERROR [!]")
                print("The Whisper AI model has not been downloaded to your computer yet.")
                print("You MUST connect to the internet and run the Voice feature at least once so it can download the model.")
                print("Once downloaded, it will work completely offline.")
                print(f"Error details: {e}\n")
                raise e
            
        # Convert audio to 16kHz float32 numpy array for Whisper (get_raw_data avoids WAV headers)
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Whisper model inference is NOT thread-safe due to PyTorch KV caches. 
        # MUST keep this inside the lock!
        result = whisper_model.transcribe(audio_np, language="en", fp16=False)
        
    return result.get("text", "").strip()

def start_continuous_listening(callback):
    """
    Starts listening in the background. Calls callback(text) whenever a phrase is transcribed.
    Returns a stop_listening function that can be called to terminate the background thread.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.2  # Wait longer before assuming the user stopped speaking
    recognizer.non_speaking_duration = 0.5
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 300  # Hardcode threshold so it doesn't accidentally cut off quiet speech
    
    mic = sr.Microphone()
    
    with mic as source:
        # Calibrate for a slightly longer duration
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        
    def listen_callback(recognizer, audio):
        def process_audio():
            text = ""
            try:
                # Try Google's free online API first
                text = recognizer.recognize_google(audio)
            except sr.RequestError:
                # Connection refused / Offline -> Fallback to Whisper
                try:
                    text = _transcribe_whisper(audio)
                except Exception as e:
                    print(f"Offline Whisper fallback failed: {e}")
            except Exception:
                pass # ignore errors on partial chunks
                
            if text:
                callback(text)
                
        threading.Thread(target=process_audio, daemon=True).start()
            
    # Remove phrase_time_limit to allow continuous recording until a natural pause
    stop_func = recognizer.listen_in_background(mic, listen_callback, phrase_time_limit=None)
    return stop_func
