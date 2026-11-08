import sqlite3
from pathlib import Path
from contextlib import closing

DB_FILE = Path(__file__).parent / "practice_logs.db"

def migrate_phase2():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        with conn:
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(practice_sessions)"
                )
            }
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            
            if "session_details" not in columns:
                conn.execute("""
                    ALTER TABLE practice_sessions
                    ADD COLUMN session_details TEXT NOT NULL DEFAULT ''
                """)
                print("Added 'session_details' column to 'practice_sessions' table.")
            else: 
                print("'session_details' column already exists in 'practice_sessions' table.")
            if "practice_partners" not in tables:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS practice_partners (
                    session_id INTEGER NOT NULL,
                    partner_user_id INTEGER NOT NULL,
                
                    PRIMARY KEY (session_id, partner_user_id),
                    FOREIGN KEY (session_id) 
                    REFERENCES practice_sessions(id) 
                    ON DELETE CASCADE
                )
                """)
                print("Created 'practice_partners' table.")
            else:
                print("'practice_partners' table already exists.")
            if "practice_characters" not in tables:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS practice_characters (
                session_id INTEGER NOT NULL,
                character_name TEXT NOT NULL COLLATE NOCASE,

                PRIMARY KEY (session_id, character_name),

                FOREIGN KEY (session_id)
                REFERENCES practice_sessions(id)
                ON DELETE CASCADE
                )
                """)
                print("Created 'practice_characters' table.")
            else:
                print("Practice characters table already exists.")

print("Migration phase 2 completed successfully.")
if __name__ == "__main__":
    migrate_phase2()