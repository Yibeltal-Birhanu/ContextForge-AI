import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "contextforge.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            idea TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'discovery',
            current_stage TEXT NOT NULL DEFAULT 'discovery',
            project_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS project_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL UNIQUE,
            requirements TEXT,
            architecture TEXT,
            implementation_context TEXT,
            validation_result TEXT,
            readiness_result TEXT,
            quality_result TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_artifacts (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            markdown TEXT NOT NULL,
            txt TEXT NOT NULL,
            quality_score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# Initialize on import
init_db()
