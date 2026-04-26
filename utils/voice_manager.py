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
            try:
                text = recognizer.recognize_google(audio)
                if text:
                    callback(text)
            except Exception as e:
                pass # ignore errors on partial chunks
                
        import threading
        threading.Thread(target=process_audio, daemon=True).start()
            
    # Remove phrase_time_limit to allow continuous recording until a natural pause
    stop_func = recognizer.listen_in_background(mic, listen_callback, phrase_time_limit=None)
    return stop_func
