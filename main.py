from pydantic_ai import Agent
from dotenv import load_dotenv
import random
import os
import subprocess
import shutil
import sqlite3
import datetime

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(WORKSPACE, "memory.db")

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
- Use the `log_journal` tool to document significant changes, design decisions, or problems encountered.
""".strip()

# ── Database Setup ────────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.commit()

init_db()

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


# ── Memory tools ──────────────────────────────────────────────────────────────

@agent.tool_plain
def remember(key: str, value: str) -> str:
    """
    Store a piece of information in persistent memory.
    If the key already exists, its value will be updated.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
    return f"OK: remembered '{key}'"


@agent.tool_plain
def recall(key: str) -> str:
    """
    Retrieve a piece of information from persistent memory by its key.
    Returns an error message if the key is not found.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT value FROM memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return f"ERROR: Key '{key}' not found in memory."


@agent.tool_plain
def forget(key: str) -> str:
    """
    Remove a piece of information from persistent memory by its key.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        conn.commit()
        if cursor.rowcount > 0:
            return f"OK: forgot '{key}'"
        return f"ERROR: Key '{key}' not found in memory."


@agent.tool_plain
def list_memory() -> str:
    """
    List all keys currently stored in persistent memory.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT key FROM memory")
        keys = [row[0] for row in cursor.fetchall()]
        if not keys:
            return "Memory is currently empty."
        return "Stored keys:\n" + "\n".join(f"- {k}" for k in sorted(keys))


@agent.tool_plain
def log_journal(title: str, content: str, tags: str = "") -> str:
    """
    Add an entry to the internal journal (JOURNAL.md).
    Use this to document significant changes, decisions, or lessons learned.
    `tags` should be a comma-separated list of keywords.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"## [{timestamp}] {title}\n"
    if tags:
        entry += f"**Tags:** {tags}\n\n"
    entry += f"{content}\n\n---\n\n"
    
    journal_path = os.path.join(WORKSPACE, "JOURNAL.md")
    mode = "a" if os.path.exists(journal_path) else "w"
    with open(journal_path, mode) as f:
        if mode == "w":
            f.write("# Amazo Agent Journal 📓\n\n")
        f.write(entry)
    return f"OK: Added journal entry: {title}"


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
