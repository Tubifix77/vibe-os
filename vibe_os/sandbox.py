"""VibeOS Computer — Docker sandbox lifecycle."""

from llm_sandbox import SandboxSession
from config import Config


class Sandbox:
    """Manages a disposable Docker container."""

    def __init__(self, cfg: Config, name: str = "playground"):
        self.cfg = cfg
        self.name = name
        self._session: SandboxSession | None = None

    def start(self):
        """Spin up a fresh container."""
        if self._session is not None:
            self.stop()
        self._session = SandboxSession(
            lang=self.cfg.container_lang,
            image=self.cfg.container_image,
            keep_template=True,
            verbose=False,
        )
        self._session.open()

    def stop(self):
        """Destroy the current container."""
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
            self._session = None

    def reset(self):
        """Kill and respawn the container."""
        self.stop()
        self.start()

    def run_command(self, cmd: str) -> tuple[str, str, int]:
        """Run a shell command in the container.

        Returns (stdout, stderr, exit_code).
        """
        if self._session is None:
            return ("", "Sandbox not running.", 1)
        try:
            import base64 as _b64
            _enc = _b64.b64encode(cmd.encode()).decode()
            result = self._session.execute_command(f"bash -c \"echo {_enc} | base64 -d | bash\"")
            stdout = result.stdout if hasattr(result, "stdout") else str(result)
            stderr = result.stderr if hasattr(result, "stderr") else ""
            code = result.exit_code if hasattr(result, "exit_code") else 0
            return (stdout, stderr, code)
        except Exception as e:
            return ("", f"Command error: {e}", 1)

    def run_code(self, code: str, libs: list[str] | None = None) -> str:
        """Run a code snippet in the container."""
        if self._session is None:
            return "[ERROR] Sandbox not running."
        try:
            result = self._session.run(code, libraries=libs or [])
            return result.stdout or ""
        except Exception as e:
            return f"[ERROR] {e}"

    def write_file(self, path: str, content: str) -> str:
        """Write a file inside the container."""
        if self._session is None:
            return "[ERROR] Sandbox not running."
        try:
            # Write to a temp file on host, copy into container
            import tempfile, os
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".tmp", delete=False
            )
            tmp.write(content)
            tmp.close()
            import os as _os
            parent = '/'.join(path.split('/')[:-1])
            if parent:
                self.run_command(f"mkdir -p '{parent}'")
            self._session.copy_to_runtime(tmp.name, path)
            os.unlink(tmp.name)
            return f"Written to {path}"
        except Exception as e:
            return f"[ERROR] {e}"

    def read_file(self, path: str) -> str:
        """Read a file from the container."""
        if self._session is None:
            return "[ERROR] Sandbox not running."
        try:
            import tempfile, os
            tmp = tempfile.mktemp(suffix=".tmp")
            self._session.copy_from_runtime(path, tmp)
            with open(tmp, "r") as f:
                data = f.read()
            os.unlink(tmp)
            return data
        except Exception as e:
            return f"[ERROR] {e}"

    def install(self, packages: list[str]) -> str:
        """Install packages in the container."""
        if self._session is None:
            return "[ERROR] Sandbox not running."
        try:
            self._session.install(packages)
            return f"Installed: {', '.join(packages)}"
        except Exception as e:
            return f"[ERROR] {e}"

    @property
    def is_running(self) -> bool:
        return self._session is not None


# ── quick self-test ──────────────────────────────────────
if __name__ == "__main__":
    cfg = Config()
    sb = Sandbox(cfg)

    print("Starting sandbox...")
    sb.start()
    print(f"Running: {sb.is_running}")

    print("\n--- run command: uname -a ---")
    out, err, code = sb.run_command("uname -a")
    print(f"stdout: {out}")
    print(f"stderr: {err}")
    print(f"exit code: {code}")

    print("\n--- write + read file ---")
    print(sb.write_file("/tmp/test.txt", "hello from brain"))
    print(sb.read_file("/tmp/test.txt"))

    print("\n--- run code ---")
    print(sb.run_code("print(2 + 2)"))

    print("\nStopping sandbox...")
    sb.stop()
    print(f"Running: {sb.is_running}")
    print("Done.")
