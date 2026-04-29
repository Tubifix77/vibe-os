"""VibeOS Computer — natural format parser."""

import re

# Match any code fence with language tag
_CODE_PATTERN = re.compile(
    r"```(\w*)\s*\n(.*?)\n\s*```",
    re.DOTALL,
)

_FILE_COMMENT = re.compile(r"^#\s*(/\S+\.\w+)")


def parse_actions(text):
    actions = []
    for m in _CODE_PATTERN.finditer(text):
        lang = m.group(1).lower()
        code = m.group(2).strip()
        if not code:
            continue
        lines = code.splitlines()

        # bash or sh = shell command
        if lang in ("bash", "sh"):
            actions.append({
                "type": "shell",
                "command": code,
            })
            continue

        # Any other lang with # /path.ext on line 1 = write file
        fm = _FILE_COMMENT.match(lines[0])
        if fm:
            path = fm.group(1)
            content = "\n".join(lines[1:])
            actions.append({
                "type": "write_file",
                "path": path,
                "content": content,
            })
    return actions


def strip_action_blocks(text):
    cleaned = _CODE_PATTERN.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


if __name__ == "__main__":
    # Test shell
    t1 = '```bash\nls -la /tmp\n```'
    a1 = parse_actions(t1)
    assert len(a1) == 1 and a1[0]["type"] == "shell"
    print("shell: PASS")

    # Test write file
    t2 = '```python\n# /tmp/hi.py\nprint("hi")\n```'
    a2 = parse_actions(t2)
    assert len(a2) == 1 and a2[0]["type"] == "write_file"
    print("write: PASS")

    # Test bash with comment (NOT write_file)
    t3 = '```bash\n# /tmp/script.sh\ndf -h\n```'
    a3 = parse_actions(t3)
    assert len(a3) == 1 and a3[0]["type"] == "shell"
    print("bash comment: PASS")

    # Test bare fence ignored
    t4 = '```\nsome output\n```'
    a4 = parse_actions(t4)
    assert len(a4) == 0
    print("bare fence: PASS")

    print("All tests passed.")