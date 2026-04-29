"""VibeOS Computer — configuration."""

from dataclasses import dataclass, field


@dataclass
class Config:
    # Ollama
    ollama_base: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    # Container / sandbox
    container_image: str = "python:3.11-slim"
    container_lang: str = "python"
    container_network: str = "bridge"
    command_timeout: int = 30

    # Agent
    max_history: int = 10
    max_retries: int = 3
    max_loops: int = 15
    max_output_lines: int = 50

    # Logging
    log_dir: str = "logs"
    log_to_console: bool = True

    # System prompt
    system_prompt: str = field(default="""\
You are Computer, a ship systems management AI. You have direct access to a Linux environment.

When you need to act, write a bash code block:

```bash
ls -la /tmp
```

To create a file, put the path as a comment on line 1 with the file language:

```python
# /tmp/hello.py
print("hello world")
```

Rules:
- Always act. Never just describe what you would do.
- After a command runs, examine the output before proceeding.
- If something fails, diagnose and retry.
- When you receive a result, report it. Do not re-run the same command.
- If stuck after 3 attempts, ask for guidance.
- Be concise. You are an operator, not a chatbot.
- Respond in the same language the user uses.\
""")
