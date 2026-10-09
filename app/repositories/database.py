import sqlite3
from pathlib import Path
from app.config import settings
from app.logging_config import logger


DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db_file = Path(DB_PATH)
    if db_file.parent and not db_file.parent.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Table for storing advisory requests and states
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisory_requests (
                request_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_data TEXT NOT NULL,
                analysis_data TEXT,
                insights_data TEXT,
                requires_human_review INTEGER DEFAULT 0,
                reviewer_comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
    logger.info(f"SQLite database initialized at {DB_PATH}", extra={"event": "db_init"})
