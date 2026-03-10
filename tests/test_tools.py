import os
import sqlite3
import pytest
from main import remember, recall, forget, list_memory, log_journal

# Setup a test database for our unit tests
DB_PATH = "test_memory.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """
    Overrides the DB_PATH in main.py with a separate test database
    to avoid modifying the real persistent memory during tests.
    """
    monkeypatch.setattr("main.DB_PATH", DB_PATH)
    # Ensure a fresh database for each test
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # Re-initialize the test database
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)"
        )
    yield
    # Cleanup after test
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_remember_and_recall():
    remember("test_key", "test_value")
    assert recall("test_key") == "test_value"

def test_recall_missing_key():
    result = recall("missing_key")
    assert "ERROR" in result

def test_forget():
    remember("to_delete", "gone soon")
    forget("to_delete")
    result = recall("to_delete")
    assert "ERROR" in result

def test_list_memory():
    remember("a", "1")
    remember("b", "2")
    result = list_memory()
    assert "- a" in result
    assert "- b" in result

def test_log_journal(tmp_path, monkeypatch):
    """
    Test the journal tool by pointing it to a temporary file.
    """
    journal_file = tmp_path / "JOURNAL.md"
    monkeypatch.setattr("main.WORKSPACE", str(tmp_path))
    
    # We need to manually set WORKSPACE because main.py calculates it at import time.
    # In main.py, journal_path = os.path.join(WORKSPACE, "JOURNAL.md")
    # So we want to make sure the journal tool writes to our tmp_path/JOURNAL.md.
    
    log_journal("Test Title", "Test Content", "test,tag")
    
    assert journal_file.exists()
    content = journal_file.read_text()
    assert "# Amazo Agent Journal" in content
    assert "Test Title" in content
    assert "Test Content" in content
    assert "test,tag" in content
