"""VibeOS Computer — structured action logger."""

import os
import json
from datetime import datetime
from config import Config


class Logger:
    """Logs all agent actions and tool results."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._file = None
        if cfg.log_dir:
            os.makedirs(cfg.log_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(cfg.log_dir, f"session_{ts}.jsonl")
            self._file = open(path, "a", encoding="utf-8")

    def log(self, event: str, **data):
        entry = {
            "time": datetime.now().isoformat(),
            "event": event,
            **data,
        }
        if self._file:
            self._file.write(json.dumps(entry) + "\n")
            self._file.flush()
        if self.cfg.log_to_console:
            short = f"[{entry['time'][11:19]}] {event}"
            detail = data.get("tool") or data.get("text", "")
            if detail:
                # truncate long output for console
                s = str(detail)
                if len(s) > 120:
                    s = s[:117] + "..."
                short += f" | {s}"
            print(short)

    def close(self):
        if self._file:
            self._file.close()
            self._file = None


if __name__ == "__main__":
    cfg = Config()
    log = Logger(cfg)
    log.log("test", text="hello world")
    log.log("tool_call", tool="shell", command="ls -la")
    log.log("tool_result", tool="shell", output="file1.txt\nfile2.txt")
    log.close()
    print("Logger test done — check logs/ folder.")
