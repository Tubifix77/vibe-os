"""VibeOS Computer — tool dispatch."""

from sandbox import Sandbox
from tool_registry import is_tool_enabled


def dispatch(tool_call: dict, sandbox: Sandbox) -> str:
    name = tool_call.get("type", tool_call.get("tool", ""))
    if not is_tool_enabled(name):
        return f"[ERROR] Tool {name} is disabled."
    if name == "shell":
        cmd = tool_call.get("command", "")
        if not cmd:
            return "[ERROR] shell: no command."
        out, err, code = sandbox.run_command(cmd)
        parts = []
        if out:
            parts.append(out)
        if err:
            parts.append(f"STDERR: {err}")
        if code != 0:
            parts.append(f"EXIT CODE: {code}")
        return "\n".join(parts) if parts else "(no output)"

    elif name == "write_file":
        path = tool_call.get("path", "")
        content = tool_call.get("content", "")
        if not path:
            return "[ERROR] write_file: no path."
        return sandbox.write_file(path, content)

    elif name == "read_file":
        path = tool_call.get("path", "")
        if not path:
            return "[ERROR] read_file: no path."
        return sandbox.read_file(path)

    elif name == "install":
        pkgs = tool_call.get("packages", [])
        if not pkgs:
            return "[ERROR] install: no packages."
        method = tool_call.get("method", "apt")
        if method == "pip":
            return sandbox.install(pkgs)
        else:
            pkg_str = " ".join(pkgs)
            out, err, code = sandbox.run_command(
                f"apt-get update -qq && apt-get install -y -qq {pkg_str}"
            )
            if code == 0:
                return f"Installed (apt): {pkg_str}"
            return f"[ERROR] apt failed:\n{err or out}"

    elif name == "download":
        url = tool_call.get("url", "")
        path = tool_call.get("path", "/tmp/download")
        if not url:
            return "[ERROR] download: no url."
        out, err, code = sandbox.run_command(
            f"wget -q -O '{path}' '{url}' 2>&1"
        )
        if code == 0:
            return f"Downloaded {url} to {path}"
        return f"[ERROR] download failed:\n{err or out}"

    elif name == "find_files":
        pattern = tool_call.get("pattern", "*")
        path = tool_call.get("path", "/")
        grep = tool_call.get("grep", "")
        if pattern == "*":
            cmd = f"find '{path}' -type f"
        else:
            cmd = f"find '{path}' -type f -name \"{pattern}\""
        cmd += " 2>/dev/null"
        if grep:
            cmd += f" | xargs grep -l '{grep}' 2>/dev/null"
        out, err, code = sandbox.run_command(cmd)
        return out.strip() if out.strip() else "(no files found)"

    elif name == "reset":
        sandbox.reset()
        return "Environment reset. Fresh container ready."

    else:
        return f"[ERROR] Unknown tool: {name}"


def format_result(tn, r, sn="playground"):
    return f"[{sn}:{tn}] {r}"
