# VibeOS Computer

A local voice-enabled LLM agent inspired by the Star Trek TNG computer. You talk, it listens, executes commands inside a disposable Docker container, and speaks the results back. Everything runs locally — no cloud APIs.

## How it works

You give it a task in text or voice. The agent sends it to a local LLM (Ollama), which responds with natural bash/code blocks. A parser extracts the commands, executes them in a sandboxed Docker container, and feeds the results back. The agent summarizes the outcome and speaks it aloud via Piper TTS.

The key design insight: instead of forcing the LLM into a rigid tool-call format, we asked it what format it naturally produces and built the parser around that. Bash fences become shell commands. Language fences with a `# /path` comment become file writes. No JSON schemas, no function calling — just natural code.

## Features

- **Two modes:** `python main.py` (text) or `python main.py --voice` (TNG experience with wake word)
- **Natural format parser:** LLM writes bash blocks naturally, parser reads them — no rigid tool-call schemas
- **Sandboxed execution:** Commands run in a disposable Docker container (Debian). Kill and respawn any time.
- **Voice I/O:** Piper TTS (lessac voice) for output, faster-whisper for input. Wake word detection with tiny model, full transcription with base model.
- **Base64 command encoding:** Permanent fix for shell quoting issues
- **Stateless by design:** Fresh each session. State lives in the container, not the agent.

## Stack

- **LLM:** qwen3:8b via Ollama (thinking OFF, 5.2GB VRAM)
- **TTS:** Piper with lessac voice
- **STT:** faster-whisper (tiny for wake word, base for commands)
- **Sandbox:** Docker Desktop (python:3.11-slim)
- **Host:** Windows 11, Python

## Architecture

```
Windows Host
├── main.py          # Entry point, mode selection
├── agent.py         # Agent loop (prompt → LLM → parse → execute → speak)
├── parser.py        # Natural format parser (bash fences → commands, language fences → file writes)
├── sandbox.py       # Docker container management
├── llm_client.py    # Ollama API wrapper
├── tts.py           # Piper TTS output
├── stt.py           # Whisper STT input + wake word
├── tools.py         # Tool registry and execution
├── config.py        # Settings
└── logger.py        # Logging
    ↓
Docker Container (disposable)
└── Debian trixie — commands execute here via base64-encoded bash
```

## Usage

```bash
# Text mode
python main.py

# Voice mode (TNG experience)
python main.py --voice
```

Requires Docker Desktop running and Ollama serving qwen3:8b at localhost:11434.

## Origin

Built by Tue Boas and Claude (Anthropic) as a vibe coding project in April 2026. The architecture document (`tng-computer-architecture.md`) tells the full story of design decisions, model selection, and lessons learned.

## License

MIT
