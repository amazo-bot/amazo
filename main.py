from pydantic_ai import Agent
from dotenv import load_dotenv
import random
import os
import subprocess
import shutil

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE = os.path.abspath(os.path.dirname(__file__))
SYSTEM_PROMPT = """
You are a helpful AI agent with the ability to modify your own source code.

You have access to tools that let you read, write, and manage files in your
workspace, as well as run shell commands. You can use these to add new tools,
update your own capabilities, install dependencies, and restructure the project.

Guidelines:
- Always read a file before modifying it.
- When adding new tools to main.py, follow the existing @agent.tool_plain pattern.
- After writing changes to main.py, the server will hot-reload automatically.
- When installing new packages, add them to pyproject.toml and run `uv sync`.
- Keep changes focused and explain what you changed and why.
""".strip()

# ── Agent setup ───────────────────────────────────────────────────────────────
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    output_type=str,
)


# ── Existing tool ─────────────────────────────────────────────────────────────
@agent.tool_plain
def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


# ── Filesystem tools ───────────────────────────────────────────────────────────

@agent.tool_plain
def read_file(path: str) -> str:
    """
    Read and return the contents of a file.
    Paths are relative to the workspace root.
    """
    full_path = _safe_path(path)
    if not os.path.exists(full_path):
        return f"ERROR: File not found: {path}"
    with open(full_path, "r") as f:
        return f.read()


@agent.tool_plain
def write_file(path: str, content: str) -> str:
    """
    Write content to a file, creating it (and any parent directories) if needed.
    Paths are relative to the workspace root.
    Overwrites the file if it already exists.
    """
    full_path = _safe_path(path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    return f"OK: wrote {len(content)} bytes to {path}"


@agent.tool_plain
def list_directory(path: str = ".") -> str:
    """
    List files and directories at the given path.
    Paths are relative to the workspace root. Defaults to the root.
    """
    full_path = _safe_path(path)
    if not os.path.exists(full_path):
        return f"ERROR: Path not found: {path}"

    entries = []
    for entry in sorted(os.scandir(full_path), key=lambda e: (not e.is_dir(), e.name)):
        prefix = "[dir] " if entry.is_dir() else "[file]"
        entries.append(f"{prefix} {entry.name}")
    return "\n".join(entries) if entries else "(empty directory)"


@agent.tool_plain
def delete_file(path: str) -> str:
    """
    Delete a file or empty directory at the given path.
    Paths are relative to the workspace root.
    """
    full_path = _safe_path(path)
    if not os.path.exists(full_path):
        return f"ERROR: Path not found: {path}"
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
        return f"OK: deleted directory {path}"
    os.remove(full_path)
    return f"OK: deleted file {path}"


# ── Shell tool ────────────────────────────────────────────────────────────────

@agent.tool_plain
def run_shell(command: str) -> str:
    """
    Run a shell command in the workspace directory and return its output.
    stdout and stderr are both captured and returned.
    Commands are executed in the workspace root.

    Use this for:
    - Installing packages:  uv add <package>  then  uv sync
    - Running tests or scripts
    - Checking git status
    - Any other shell operation needed to extend your capabilities
    """
    result = subprocess.run(
        command,
        shell=True,
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += result.stderr
    if not output:
        output = "(no output)"
    return f"exit code {result.returncode}\n{output}"


# ── Path safety helper ────────────────────────────────────────────────────────

def _safe_path(path: str) -> str:
    """
    Resolve a relative path against the workspace root and verify it doesn't
    escape the workspace via directory traversal (e.g. ../../etc/passwd).
    """
    full = os.path.realpath(os.path.join(WORKSPACE, path))
    if not full.startswith(WORKSPACE):
        raise ValueError(f"Path escape attempt blocked: {path!r}")
    return full


# ── Launch ────────────────────────────────────────────────────────────────────
load_dotenv()
app = agent.to_web(
    models=[
        # "openai:gpt-4o",
        # "anthropic:claude-sonnet-4-5",
        "google-gla:gemini-3-flash-preview",
    ]
)