TOOL_REGISTRY = [
    {
        "name": "shell",
        "enabled": True,
        "desc": '- shell: Run a command.\n'
            '  {"tool": "shell", "command": "ls"}',
    },
    {
        "name": "write_file",
        "enabled": True,
        "desc": '- write_file: Create a file.\n'
            '  {"tool": "write_file", "path": "/tmp/f.py",'
            ' "content": "print(1)"}',
    },
    {
        "name": "read_file",
        "enabled": True,
        "desc": '- read_file: Read a file.\n'
            '  {"tool": "read_file", "path": "/tmp/f.py"}',
    },
    {
        "name": "install",
        "enabled": True,
        "desc": '- install: Install packages.\n'
            '  {"tool": "install", "packages": ["curl"]}',
    },
    {
        "name": "download",
        "enabled": True,
        "desc": '- download: Fetch a URL.\n'
            '  {"tool": "download", "url": "https://x.com/f",'
            ' "path": "/tmp/f"}',
    },
    {
        "name": "find_files",
        "enabled": True,
        "desc": '- find_files: Search files.\n'
            '  {"tool": "find_files", "pattern": "*.py"}',
    },
    {
        "name": "reset",
        "enabled": True,
        "desc": '- reset: Destroy and recreate.\n'
            '  {"tool": "reset"}',
    },
]


def get_enabled_tools():
    return [t for t in TOOL_REGISTRY if t["enabled"]]


def get_tool_descriptions():
    parts = [t["desc"] for t in get_enabled_tools()]
    return "\n\n".join(parts)


def is_tool_enabled(name):
    for t in TOOL_REGISTRY:
        if t["name"] == name:
            return t["enabled"]
    return False
