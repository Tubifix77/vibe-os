"""VibeOS Computer — agent loop."""

from config import Config
from llm_client import chat_stream
from parser import parse_actions, strip_action_blocks
from tools import dispatch
from sandbox import Sandbox
from logger import Logger
from tts import speak
from tool_registry import get_tool_descriptions




def truncate_output(text, max_lines):
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    kept = lines[-max_lines:]
    dropped = len(lines) - max_lines
    h = f"[output truncated: showing last {max_lines} of {len(lines)} lines]"
    return h + "\n" + "\n".join(kept)


class Agent:
    """The brain. Sends tasks to the LLM, parses tool calls,
    executes them in the sandbox, feeds results back."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.sandbox = Sandbox(cfg)
        self.logger = Logger(cfg)
        self.history: list[dict] = []

    def start(self):
        """Spin up the sandbox and prepare for tasks."""
        print("Starting sandbox...")
        self.sandbox.start()
        print("Scanning environment...")
        env_summary = self._scan_environment()
        if env_summary:
            self.history.append({
                "role": "system",
                "content": f"[Environment scan]\n{env_summary}",
            })
        print("Sandbox ready.\n")
        speak("VibeOS online. All systems nominal.")
        self.logger.log("session_start", model=self.cfg.ollama_model)

    def stop(self):
        """Tear down everything."""
        speak("VibeOS shutting down.")
        self.sandbox.stop()
        self.logger.log("session_end")
        self.logger.close()
        print("Sandbox stopped. Session ended.")

    def run_task(self, user_input: str):
        """Process one user task through the agent loop."""
        self.logger.log("user_input", text=user_input)
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()

        loop_count = 0
        while loop_count < self.cfg.max_loops:
            loop_count += 1

            # Build messages for LLM
            messages = [
                {"role": "system", "content": self.cfg.system_prompt},
                *self.history,
            ]

            # Get LLM response (streams to console)
            print("\n--- Computer ---")
            response = chat_stream(self.cfg, messages)
            print()

            if not response or response.startswith("[ERROR]"):
                self.logger.log("llm_error", text=response)
                print(response)
                break

            # Parse for tool calls
            calls = parse_actions(response)
            prose = strip_action_blocks(response)

            if not calls:
                # No tool calls — LLM is done, just talking
                self.history.append({
                    "role": "assistant",
                    "content": response,
                })
                self.logger.log("llm_response", text=prose)
                if prose:
                    speak(prose)
                break

            # There are tool calls — execute them one at a time
            self.history.append({
                "role": "assistant",
                "content": response,
            })
            self.logger.log("llm_response", text=prose)

            for action in calls:
                atype = action.get("type", "unknown")
                self.logger.log("action", type=atype, args=action)

                result = dispatch(action, self.sandbox)

                self.logger.log("action_result", type=atype, output=result)
                print(f"\n[{self.sandbox.name}:{atype}] {result}\n")

                self.history.append({
                    "role": "user",
                    "content": f"[Result: {atype}]\n{truncate_output(result, self.cfg.max_output_lines)}",
                })

            self._trim_history()
            # Loop continues — LLM will see tool results and decide
            # whether to run more tools or respond with prose.

        if loop_count >= self.cfg.max_loops:
            msg = f"Reached max loop count ({self.cfg.max_loops}). Stopping."
            print(msg)
            self.logger.log("max_loops", text=msg)
            speak("Unable to comply. Operation exceeded maximum attempts.")

    def _scan_environment(self) -> str:
        cmds = [
            ("OS", "cat /etc/os-release | grep PRETTY_NAME"),
            ("Kernel", "uname -r"),
            ("Disk", "df -h / | tail -1"),
            ("Users", "ls /home 2>/dev/null || echo '(none)'"),
            ("Files in /tmp", "ls /tmp 2>/dev/null || echo '(empty)'"),
        ]
        parts = []
        for label, cmd in cmds:
            out, err, code = self.sandbox.run_command(cmd)
            val = out.strip() if out.strip() else "(unavailable)"
            parts.append(f"{label}: {val}")
        return "\n".join(parts)

    def _trim_history(self):
        """Keep only the last N exchange pairs."""
        max_msgs = self.cfg.max_history * 2
        if len(self.history) > max_msgs:
            self.history = self.history[-max_msgs:]


if __name__ == "__main__":
    cfg = Config()
    agent = Agent(cfg)
    agent.start()
    agent.run_task("List the contents of the root directory.")
    agent.stop()
