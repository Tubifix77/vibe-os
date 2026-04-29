"""VibeOS Computer — entry point."""

import sys
from config import Config
from agent import Agent

VOICE = "--voice" in sys.argv


def main():
    cfg = Config()
    if VOICE:
        from stt import wait_for_wake, listen_command

    print("=" * 50)
    print("  VibeOS Computer — Phase 4")
    m = "Voice" if VOICE else "Text"
    print(f"  Mode: {m}")
    print(f"  Model: {cfg.ollama_model}")
    print("=" * 50)
    if not VOICE:
        print("  Type a task, or 'quit' to exit.")
        print("  Type 'reset' to respawn.")
    else:
        print("  Say 'Computer' to activate.")
    print("=" * 50)
    print()

    agent = Agent(cfg)
    try:
        agent.start()
        while True:
            try:
                if VOICE:
                    wait_for_wake()
                    user = listen_command()
                    if not user:
                        continue
                    print(f"Crew > {user}")
                else:
                    user = input("\nCrew > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user:
                continue
            if user.lower() in ("quit", "exit"):
                break
            if user.lower() == "reset":
                agent.sandbox.reset()
                print("Container reset.")
                continue
            agent.run_task(user)
    finally:
        agent.stop()


if __name__ == "__main__":
    main()