import io
import os
import tempfile
from gtts import gTTS
import speech_recognition as sr

def text_to_speech(text: str) -> bytes:
    tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()

def speech_to_text(audio_bytes: bytes) -> str:
    r = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name
    try:
        with sr.AudioFile(tmp) as source:
            audio = r.record(source)
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    finally:
        try:
            os.unlink(tmp)
        except:
            pass
