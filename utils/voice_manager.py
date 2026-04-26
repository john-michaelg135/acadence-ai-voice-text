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
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
    def listen_callback(recognizer, audio):
        try:
            text = recognizer.recognize_google(audio)
            if text:
                callback(text)
        except Exception as e:
            pass # ignore errors on partial chunks
            
    # phrase_time_limit determines how long a single block of speech can be before it forces a transcription
    stop_func = recognizer.listen_in_background(mic, listen_callback, phrase_time_limit=15)
    return stop_func
