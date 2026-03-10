# Amazo Agent 🤖

An autonomous AI agent capable of modifying its own source code, managing its workspace, and maintaining persistent memory.

## 🚀 Capabilities

- **Self-Modification:** The agent can read, write, and update its own `main.py` and other source files.
- **Filesystem Management:** Full access to list, read, write, and delete files within the workspace.
- **Shell Execution:** Can run arbitrary shell commands to install dependencies (`uv`), run tests, or manage git.
- **Persistent Memory:** Uses a local SQLite database (`memory.db`) to store and recall information across sessions.
- **Autobiographical Journal:** Maintains a `JOURNAL.md` to track significant changes and decisions.
- **Containerized Environment:** Runs inside a Docker container for a consistent and isolated development environment.
- **Hot-Reloading:** Any changes the agent makes to its code are automatically reloaded by the Uvicorn server.

## 🛠 Tools

### Memory & Journaling
- `remember(key, value)`: Store information in SQLite.
- `recall(key)`: Retrieve stored information.
- `forget(key)`: Delete a memory.
- `list_memory()`: List all stored keys.
- `log_journal(title, content, tags)`: Add an entry to the internal `JOURNAL.md`.

### Filesystem
- `read_file(path)`: Get file content.
- `write_file(path, content)`: Create or update files.
- `list_directory(path)`: Explore the workspace.
- `delete_file(path)`: Remove files or directories.

### System
- `run_shell(command)`: Execute terminal commands.
- `roll_dice()`: A simple utility for random numbers.

## 📦 Getting Started

1. Ensure Docker is installed.
2. Configure your `.env` file with `GOOGLE_API_KEY` (or other model providers) and `GITHUB_TOKEN`.
3. Run `./run_interface.sh` to build the container and start the agent.
4. Access the chat interface at `http://localhost:8000`.

## 📈 Roadmap

The agent maintains its own internal roadmap in its persistent memory. Current priorities include:
1. **Semantic Search:** RAG-based indexing for larger projects.
2. **GitHub Integration:** Automating repository management via the GitHub API.
3. **Self-Testing Framework:** Automated verification of code changes.
