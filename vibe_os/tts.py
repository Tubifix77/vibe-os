"""VibeOS Computer — text-to-speech via Piper."""

import subprocess
import tempfile
import os
import sounddevice as sd
import soundfile as sf

VOICE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "voices",
    "en_US-lessac-medium.onnx",
)


def speak(text: str):
    if not text or not text.strip():
        return
    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False)
    tmp.close()
    try:
        r = subprocess.run(
            ["python", "-m", "piper",
             "--model", VOICE,
             "--output_file", tmp.name],
            input=text.encode(),
            capture_output=True)
        if r.returncode != 0:
            return
        data, rate = sf.read(tmp.name)
        sd.play(data, rate)
        sd.wait()
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


if __name__ == "__main__":
    speak("Computer online. All systems nominal.")
    print("Done.")