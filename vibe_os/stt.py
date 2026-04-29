"""VibeOS Computer — speech-to-text via faster-whisper."""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

RATE = 16000
MIC_RATE = 44100
WAKE_WORD = "computer"
SILENCE_THRESHOLD = 0.02
SILENCE_DURATION = 1.5  # seconds
WAKE_CHUNK = 2  # seconds per wake listen
MAX_LISTEN = 15  # max seconds for command

# Load tiny model for wake word (fast, low quality)
# Load small model for commands (slower, better)
_wake_model = None
_cmd_model = None


def _get_wake_model():
    global _wake_model
    if _wake_model is None:
        print("Loading wake word model...", flush=True)
        print("Ready. Say Computer...", flush=True)
        _wake_model = WhisperModel(
            "tiny", device="cpu", compute_type="int8")
    return _wake_model


def _get_cmd_model():
    global _cmd_model
    if _cmd_model is None:
        print("Loading command model...", flush=True)
        _cmd_model = WhisperModel(
            "base", device="cpu", compute_type="int8")
    return _cmd_model


def record_chunk(duration):
    """Record audio for given duration, return numpy array."""
    audio = sd.rec(
        int(duration * MIC_RATE),
        samplerate=MIC_RATE,
        channels=1,
        dtype="float32")
    sd.wait()
    a = audio.flatten()
    n = int(len(a) * RATE / MIC_RATE)
    from scipy.signal import resample
    return resample(a, n).astype(np.float32)


def record_until_silence():
    chunks = []
    silent = 0
    needed = int(SILENCE_DURATION / 0.5)
    print("  [listening]", flush=True)
    for _ in range(int(MAX_LISTEN / 0.5)):
        c = record_chunk(0.5)
        chunks.append(c)
        if np.max(np.abs(c)) < SILENCE_THRESHOLD:
            silent += 1
            if silent >= needed:
                break
        else:
            silent = 0
    return np.concatenate(chunks)


def transcribe(audio, model):
    segs, _ = model.transcribe(audio, beam_size=1, language="en")
    return " ".join(s.text for s in segs).strip()


def wait_for_wake():
    import time
    time.sleep(0.5)
    """Listen for wake word. Returns True when heard."""
    m = _get_wake_model()
    while True:
        audio = record_chunk(WAKE_CHUNK)
        text = transcribe(audio, m).lower()
        if WAKE_WORD in text:
            return True


def listen_command():
    """Record and transcribe a command after wake word."""
    m = _get_cmd_model()
    audio = record_until_silence()
    text = transcribe(audio, m)
    return text


if __name__ == "__main__":
    print("Say 'Computer' to activate...")
    wait_for_wake()
    print("Wake word detected!")
    print("Speak your command...")
    cmd = listen_command()
    print(f"You said: {cmd}")