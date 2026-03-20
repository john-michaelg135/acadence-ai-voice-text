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
            # Listen for up to 5 seconds before giving up, and cut off after 10 seconds of speech
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        # Call out to Google Web Speech API (Free, default limit applies)
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        print("Listening timed out.")
        return ""
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""
    except Exception as e:
        print(f"Error during voice recognition: {e}")
        return ""
