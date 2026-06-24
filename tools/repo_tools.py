from pathlib import Path

MAX_SEARCH_RESULTS = 30
MAX_FILE_SIZE = 50_000  # chars


def read_file(repo_path: str, relative_path: str) -> str:
    path = Path(repo_path) / relative_path
    if not path.exists():
        return f"ERROR: File not found: {relative_path}"
    content = path.read_text(errors="replace")
    if len(content) > MAX_FILE_SIZE:
        content = content[:MAX_FILE_SIZE] + "\n... [truncated]"
    return content


def write_file(repo_path: str, relative_path: str, content: str) -> str:
    path = Path(repo_path) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return f"OK: Written {len(content)} chars to {relative_path}"


def list_files(repo_path: str, extension: str = "") -> list[str]:
    root = Path(repo_path)
    pattern = f"**/*{extension}" if extension else "**/*"
    files = [
        str(p.relative_to(root))
        for p in root.glob(pattern)
        if p.is_file() and ".git" not in p.parts
    ]
    return sorted(files)


def search_in_files(repo_path: str, search_term: str) -> list[str]:
    root = Path(repo_path)
    matches: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if search_term.lower() in line.lower():
                    rel = path.relative_to(root)
                    matches.append(f"{rel}:{i}: {line.strip()}")
                    if len(matches) >= MAX_SEARCH_RESULTS:
                        return matches
        except Exception:
            continue
    return matches


# Anthropic-format tool definitions passed directly to the Claude API
TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file in the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Absolute path to the repo root"},
                "relative_path": {"type": "string", "description": "Path relative to repo root"},
            },
            "required": ["repo_path", "relative_path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file in the repository with new content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Absolute path to the repo root"},
                "relative_path": {"type": "string", "description": "Path relative to repo root"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["repo_path", "relative_path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List all files in the repository, optionally filtered by extension.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Absolute path to the repo root"},
                "extension": {"type": "string", "description": "File extension filter e.g. '.java'", "default": ""},
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "search_in_files",
        "description": "Search for a term across all files in the repository. Returns file:line: text matches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Absolute path to the repo root"},
                "search_term": {"type": "string", "description": "Term to search for"},
            },
            "required": ["repo_path", "search_term"],
        },
    },
]

TOOL_DISPATCH = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "search_in_files": search_in_files,
}
