# tng-computer-architecture
## A local voice-enabled LLM agent controlling a disposable OS, inspired by Star Trek TNG

**Author:** Tue Boas + Claude  
**Started:** 2026-04-26  
**Status:** Phase 3 COMPLETE — Voice Output  
**Hardware target:** Windows 11, Intel i5-9600K, RTX 3080 10GB, 16GB RAM  

---

## 1. Vision

An LLM-powered agent that controls a disposable Linux environment and speaks its answers aloud. You give it tasks, it executes them silently — running commands, writing files, installing software — inside a sandboxed Docker container, then speaks the result in a calm, authoritative voice.

**Core design principle:** The Computer is a STATELESS UTILITY. Fresh each session, no conversation memory. State lives in the environment (the container), not in the Computer. It is a sidecar/interface layer that does not own the systems it controls.

**Long-term vision:** Voice input (STT + wake word) added in Phase 4. Brain on dedicated NPU/TPU hardware eventually.

---

## 2. Design Principles

**Brain and playground are separate.** Agent on Windows host, sandbox in Docker container.

**Local-first.** Ollama for LLM, Piper for TTS, Docker for containers. No cloud APIs.

**Let the LLM be natural.** Don't force artificial formats. We asked the LLM what format it naturally produces and built the parser around that. bash blocks for commands, language-specific fences for file creation. (Phase 2 insight.)

**Voice follows the TNG pattern.** The Computer speaks its final answer. Silent during tool execution. Startup and shutdown announcements. Error states spoken aloud.

**Simple until proven insufficient.** A Python program with a loop. No frameworks.

---

## 3. Hardware

| Resource | Spec | Implication |
|---|---|---|
| CPU | Intel i5-9600K @ 3.70GHz (6 cores) | TTS + future STT run here |
| GPU | RTX 3080, 10GB VRAM | LLM (qwen3:8b, 5.2GB) |
| RAM | 16GB DDR4 @ 3200 MT/s | ~6GB free for brain + Docker |
| OS | Windows 11 Pro (25H2) | Docker Desktop uses WSL2 |
| Audio | NVIDIA HDMI → M32UC monitor speakers | TTS output via sounddevice |

---

## 4. Model Selection

**Selected: `qwen3:8b`** (5.2GB, thinking mode OFF)

| | gemma3:12b | qwen2.5-coder:7b | qwen3:8b (no think) |
|---|---|---|---|
| Speed | 20-60s/task | 5-10s | 5-10s |
| Tool format | Drifts | Correct | Natural bash blocks |
| Language | English | Danish (stuck) | English |
| Narration | Very chatty | Moderate | Minimal |

Key insight: stronger system prompt + thinking off beats thinking on + weaker prompt.

---

## 5. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    WINDOWS HOST                       │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐        │
│  │  OLLAMA  │  │  PIPER   │  │    BRAIN     │        │
│  │ qwen3:8b │  │  TTS     │  │   (Python)   │        │
│  │ :11434   │  │ lessac   │  │              │        │
│  └────┬─────┘  └────┬─────┘  │ - Agent loop │        │
│       │              │        │ - Parser     │        │
│       └──────┬───────┘        │ - History    │        │
│              │                └──────┬───────┘        │
│              ◄───────────────────────┘                │
│                              │                        │
│                     Docker API                        │
│                              │                        │
│  ┌───────────────────────────▼────────────────────┐   │
│  │         PLAYGROUND CONTAINER                    │   │
│  │         Debian trixie (python:3.11-slim)        │   │
│  │         Commands via base64-encoded bash         │   │
│  │         Disposable — kill and respawn any time   │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 6. The Natural Format Parser

Instead of JSON tool calls, the LLM writes natural code blocks:

**Shell commands** — ` ```bash ` fence:
````
```bash
ls -la /tmp && df -h
```
````

**File creation** — language-specific fence with `# /path.ext` on line 1:
````
```python
# /tmp/hello.py
print("hello world")
```
````

Parser rules:
- ` ```bash ` or ` ```sh ` → always shell (even if first line has `# /path`)
- Any other language fence with `# /path.ext` on line 1 → write_file
- Bare fences (no language tag) → ignored (LLM showing example output)
- No code blocks → prose response (spoken aloud)

The path must have a file extension (`.py`, `.txt`, `.md`, etc.) to trigger write_file.

Commands are base64-encoded before execution, permanently solving all quoting issues.

---

## 7. Voice System (Phase 3)

**TTS Engine:** Piper with `en_US-lessac-medium` voice (chosen for its calm, lower tone reminiscent of the TNG Computer voice).

**Voice rules (TNG pattern):**
- Startup: "VibeOS online. All systems nominal."
- Shutdown: "VibeOS shutting down."
- Final answer (prose with no code blocks): spoken aloud
- During tool execution: silent
- Max loops error: "Unable to comply. Operation exceeded maximum attempts."

**Audio pipeline:** Piper generates WAV → soundfile reads it → sounddevice plays to default output.

Voice runs on the Windows host alongside the brain. Not containerized — needs direct speaker access.

---

## 8. Agent Loop

```
1. Receive task (console input)
2. Build prompt: system prompt + conversation history + task
3. Send to Ollama (streaming, think: false)
4. Parse response for code blocks:
   - ```bash → shell action
   - ```python/other with # /path.ext → write_file action
   - No code blocks → final prose answer → SPEAK IT
5. Execute action in container (base64-encoded bash)
6. Feed result back to LLM (truncated to 50 lines)
7. Repeat from 3 until prose response
8. Wait for next task
```

---

## 9. Tool Registry (future seam)

`tool_registry.py` maintains named tools with enabled flags. Not currently used for dispatch (natural parser handles everything), but exists for:
- Disabling capabilities for smaller models
- Model-specific profiles
- Runtime toggle via console or future GUI

---

## 10. Error Handling

| Failure | Response |
|---|---|
| No code blocks in LLM output | Prose response, spoken aloud |
| Shell command fails | stderr fed back to LLM for diagnosis |
| Container crashes | Auto-respawn, inform LLM |
| LLM loops (>15 iterations) | Force stop, speak "Unable to comply" |
| Ollama/Docker not running | Detected at startup, exit |
| LLM re-runs same command | System prompt rule: "report result, don't re-run" |

---

## 11. File Structure

```
vibe_os/
├── main.py              # Entry point, console loop
├── config.py            # Settings, system prompt
├── agent.py             # Agent loop, env scan, voice integration
├── tools.py             # Action dispatch (shell + write_file)
├── tool_registry.py     # Tool registry (future seam)
├── llm_client.py        # Ollama streaming client (think: false)
├── sandbox.py           # Container lifecycle (base64 bash, mkdir -p)
├── parser.py            # Natural format parser (bash + language fences)
├── tts.py               # Piper TTS with lessac voice
├── logger.py            # JSONL session logging
├── voices/              # Piper voice models (.onnx + .json)
└── logs/                # Session log files
```

---

## 12. Dependencies

### Host (Python, pip install --user)
- `llm-sandbox[docker]`, `requests`, `piper-tts`, `sounddevice`, `soundfile`

### Infrastructure
- Docker Desktop (WSL2), Ollama with qwen3:8b

---

## 13. Phase Roadmap

| Phase | Scope | Status |
|---|---|---|
| **0 — MVP** | Text agent + Docker sandbox, 5 JSON tools | COMPLETE |
| **1 — Better Operator** | Truncation, env scan, 7 tools, registry, model selection | COMPLETE |
| **2 — Natural Format** | Bash-block parser, language-specific file fences | COMPLETE |
| **3 — Voice Output** | Piper TTS, lessac voice, startup/shutdown/error speech | COMPLETE |
| **4 — Voice Input** | Wake word + STT (microphone → text → agent) | Not started |
| **5 — Self-hosting** | Brain on dedicated hardware (NPU/TPU) | Not started |

---

## 14. Testing Results

### Phases 0-1 (gemma3:12b → qwen3:8b)
All pass: shell, multi-step chaining, apt install, file I/O, error recovery, diagnose-fix-retry, container reset, destructive confirmation, env scan, output truncation.

### Phase 2 (natural format)
All pass: bash blocks, write_file detection, multi-file projects, combined install+curl in single block.

### Phase 3 (voice)
- Startup announcement: PASS
- Shutdown announcement: PASS  
- Spoken final answer: PASS
- Silent during tool execution: PASS
- Max loops error speech: PASS
- Loop fix (don't re-run same command): PASS
- Parser fix (bash fence = always shell, not write_file): PASS

---

## Appendix: Why Natural Format Beats JSON Tool Calls

Phase 0/1 forced `{"tool": "shell", "command": "ls"}` in special fences. Problems: format drift across models, complex system prompts, JSON parse errors, quoting collisions.

Phase 2 asked: what does the LLM naturally produce? Answer: code blocks. Building the parser around the model's natural output eliminates format drift. The parser is 30 lines of regex. The system prompt is half the size.

Phase 3 maps perfectly to voice: the LLM's prose responses are what gets spoken. Code blocks are silent execution. No translation layer needed.

---

---

## Project Complete — 2026-04-28

Built in three days across four sessions. From a naive architecture document to a working voice-controlled AI agent managing a disposable Linux sandbox.

**What we built:** A local TNG-style Computer that listens for "Computer", transcribes your command, sends it to a local LLM, executes actions silently in a Docker container, and speaks the result aloud in a calm female voice. No cloud. No API keys. Everything runs on one Windows PC with a gaming GPU.

**What we learned:**
- Ask the LLM what format it wants to produce, then build the parser around that. Don't force your format on the model.
- A stronger system prompt with thinking off beats thinking on with a weaker prompt.
- The Computer is a stateless utility, not an assistant with memory. State lives in the environment.
- Brain and playground must be separate. The Computer should never be able to kill itself.
- Always keep Phase 5+ in mind when building Phase 0. It shapes every decision.
- The simplest bug is always the headset being turned off.

**The crew of this project:**
- Tue Boas — vision, testing, the "ask the LLM what's natural" insight, creative direction
- Claude — architecture, implementation, debugging, documentation

*"Computer online. All systems nominal."*
