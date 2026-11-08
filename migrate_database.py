
import sqlite3
from pathlib import Path
from contextlib import closing

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "practice_logs.db"

def migrate_database():

    if not DB_FILE.exists():
        raise FileNotFoundError("Database not found")

    with closing(sqlite3.connect(DB_FILE)) as conn:

        columns = conn.execute(
                """
                PRAGMA table_info(practice_sessions)
                """,
            ).fetchall()

        column_exists = False
        
        for column in columns:
            if column[1] == "interaction_id":
                column_exists = True
        with conn:
            conn.execute("BEGIN")
            if not column_exists:
                conn.execute(
                    """
                    ALTER TABLE practice_sessions
                    ADD COLUMN interaction_id TEXT;
                 """,
                )
                print("Interaction ID column added")
            else:
                print("Interaction ID column already exists.")

            conn.execute(
                '''CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_interaction_id 
                ON practice_sessions (interaction_id)''')

if __name__ == "__main__":
    migrate_database()