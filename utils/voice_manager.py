import speech_recognition as sr
import threading
import queue
from typing import Optional, Callable
from utils.logger import logger

# Configuration constants
DEFAULT_AUDIO_TIMEOUT = 10  # seconds
DEFAULT_PHRASE_TIME_LIMIT = 30  # seconds
DEFAULT_PAUSE_THRESHOLD = 1.2  # seconds
DEFAULT_ENERGY_THRESHOLD = 300

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
            audio = recognizer.listen(source, timeout=DEFAULT_AUDIO_TIMEOUT, phrase_time_limit=DEFAULT_PHRASE_TIME_LIMIT)
            
        # Call out to Google Web Speech API (Free, default limit applies)
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        logger.warning("Listening timed out.")
        return ""
    except sr.UnknownValueError:
        logger.warning("Google SpeechRecognition could not understand audio.")
        return ""
    except sr.RequestError as e:
        logger.error(f"Could not request results from Google SpeechRecognition service: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error during voice recognition: {e}", exc_info=True)
        return ""


class WhisperInferenceWorker:
    """
    Thread-safe Whisper inference worker using a queue-based design.
    Ensures PyTorch inference happens on a single thread.
    """
    
    def __init__(self):
        self.request_queue: queue.Queue = queue.Queue()
        self.result_dict: dict = {}
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event: threading.Event = threading.Event()
        self.model = None
        self._start_worker()
        logger.debug("WhisperInferenceWorker initialized")
    
    def _start_worker(self):
        """Start the worker thread that handles all Whisper inference."""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Worker thread's main loop - processes inference requests."""
        try:
            import whisper
            import numpy as np
            logger.info("Loading Whisper model (small.en)...")
            self.model = whisper.load_model("small.en")
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("Please install whisper: pip install -U openai-whisper setuptools-rust")
            return
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
            logger.error("CRITICAL: Whisper AI model download failed. Ensure internet connection on first run.")
            return
        
        while not self.shutdown_event.is_set():
            try:
                # Wait for requests with timeout to allow clean shutdown
                request_id, audio_data = self.request_queue.get(timeout=1.0)
                
                if request_id is None:  # Shutdown signal
                    break
                
                try:
                    import numpy as np
                    # Convert audio to 16kHz float32 numpy array for Whisper
                    raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
                    audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # PyTorch inference (thread-safe because it's on this single worker thread)
                    result = self.model.transcribe(audio_np, language="en", fp16=False)
                    text = result.get("text", "").strip()
                    
                    self.result_dict[request_id] = {"success": True, "text": text}
                except Exception as e:
                    logger.error(f"Whisper transcription failed: {e}", exc_info=True)
                    self.result_dict[request_id] = {"success": False, "error": str(e)}
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
    
    def transcribe_async(self, audio_data, request_id: str) -> None:
        """Queue an audio chunk for async transcription."""
        self.request_queue.put((request_id, audio_data))
    
    def get_result(self, request_id: str, timeout: float = 30.0) -> dict:
        """
        Wait for transcription result with timeout.
        Returns {"success": bool, "text": str} or {"success": False, "error": str}
        """
        start_time = threading.current_thread()
        while threading.current_thread() != self.worker_thread:
            if request_id in self.result_dict:
                result = self.result_dict.pop(request_id)
                return result
            
            if threading.current_thread() != self.worker_thread:
                import time
                time.sleep(0.1)  # Brief sleep to avoid busy waiting
                
                elapsed = threading.current_thread() - start_time if hasattr(threading.current_thread(), '__sub__') else timeout
                if elapsed > timeout:
                    return {"success": False, "error": "Transcription timeout"}
        
        return {"success": False, "error": "Worker thread not ready"}
    
    def shutdown(self):
        """Gracefully shutdown the worker thread."""
        logger.debug("Shutting down WhisperInferenceWorker")
        self.shutdown_event.set()
        self.request_queue.put((None, None))  # Signal to shutdown
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)


# Global worker instance
_whisper_worker: Optional[WhisperInferenceWorker] = None
_worker_lock = threading.Lock()

def _get_whisper_worker() -> WhisperInferenceWorker:
    """Get or create the global Whisper worker (lazy initialization)."""
    global _whisper_worker
    if _whisper_worker is None:
        with _worker_lock:
            if _whisper_worker is None:
                try:
                    _whisper_worker = WhisperInferenceWorker()
                except Exception as e:
                    logger.error(f"Failed to initialize Whisper worker: {e}", exc_info=True)
                    raise
    return _whisper_worker

def _transcribe_whisper(audio_data):
    """
    Transcribes audio using Whisper with proper thread safety.
    Uses queue-based worker to avoid thread-unsafe PyTorch inference.
    """
    try:
        import uuid
        request_id = str(uuid.uuid4())
        worker = _get_whisper_worker()
        worker.transcribe_async(audio_data, request_id)
        result = worker.get_result(request_id, timeout=30.0)
        
        if result.get("success"):
            return result.get("text", "")
        else:
            logger.error(f"Whisper transcription error: {result.get('error')}")
            return ""
    except Exception as e:
        logger.error(f"Error in _transcribe_whisper: {e}", exc_info=True)
        return ""


def start_continuous_listening(callback: Callable[[str], None]):
    """
    Starts listening in the background. Calls callback(text) whenever a phrase is transcribed.
    Returns a stop_listening function that can be called to terminate the background thread.
    Properly manages microphone resource cleanup.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = DEFAULT_PAUSE_THRESHOLD
    recognizer.non_speaking_duration = 0.5
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = DEFAULT_ENERGY_THRESHOLD
    
    # Wrap microphone in try-finally to ensure cleanup
    mic: Optional[sr.Microphone] = None
    stop_func = None
    
    try:
        mic = sr.Microphone()
        
        with mic as source:
            # Calibrate for a slightly longer duration
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        def listen_callback(recognizer, audio):
            """Process transcribed audio in background thread."""
            def process_audio():
                text = ""
                try:
                    # Try Google's free online API first
                    text = recognizer.recognize_google(audio)
                except sr.RequestError as e:
                    # Connection refused / Offline -> Fallback to Whisper
                    try:
                        text = _transcribe_whisper(audio)
                    except Exception as e:
                        logger.warning(f"Offline Whisper fallback failed: {e}")
                except sr.UnknownValueError:
                    logger.debug("Could not understand audio")
                except Exception as e:
                    logger.error(f"Error processing audio: {e}", exc_info=True)
                
                if text:
                    try:
                        callback(text)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}", exc_info=True)
            
            # Process in background thread to not block listening
            threading.Thread(target=process_audio, daemon=True).start()
        
        # Remove phrase_time_limit to allow continuous recording until a natural pause
        stop_func = recognizer.listen_in_background(mic, listen_callback, phrase_time_limit=None)
        logger.info("Continuous listening started")
        
    except Exception as e:
        logger.error(f"Failed to start continuous listening: {e}", exc_info=True)
        if mic:
            try:
                mic.__exit__(None, None, None)
            except Exception:
                pass
        raise
    
    # Return a stop function that properly cleans up resources
    def stop_listening():
        """Stop listening and clean up microphone resources."""
        try:
            if stop_func:
                # wait_for_stop=True ensures the background listener thread
                # finishes before we close the microphone stream, preventing
                # OSError -9983 (stream stopped) and -9988 (stream closed)
                try:
                    stop_func(wait_for_stop=True)
                except OSError as e:
                    # Suppress expected stream teardown errors
                    logger.debug(f"Expected stream teardown error (harmless): {e}")
            if mic:
                try:
                    mic.__exit__(None, None, None)
                except OSError as e:
                    # Stream may already be closed by the recognizer — this is normal
                    logger.debug(f"Microphone already closed (harmless): {e}")
                except Exception as e:
                    logger.warning(f"Error closing microphone: {e}")
            logger.info("Continuous listening stopped")
        except Exception as e:
            logger.error(f"Error stopping listening: {e}", exc_info=True)
    
    return stop_listening

