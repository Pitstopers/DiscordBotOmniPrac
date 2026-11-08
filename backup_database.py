import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime
from tempfile import TemporaryDirectory


BASE_DIR = Path(__file__).resolve().parent

ctime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


DB_FILE = BASE_DIR / "practice_logs.db"

BACKUP_DIR = BASE_DIR / "backups"

def backup_database():
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_FILE}"
        )
    print("All is well")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_file = BACKUP_DIR / f"Backup_Database{ctime}.db"

    if backup_file.exists():
        raise FileExistsError("Backup file already exists")

    with closing(sqlite3.connect(DB_FILE)) as source:
        with closing(sqlite3.connect(backup_file)) as destination:
            source.backup(destination)

    with closing(sqlite3.connect(backup_file)) as verify_conn:

        check = verify_conn.execute(
            "PRAGMA integrity_check;"
            ).fetchone()
        if check[0] != "ok":
            raise RuntimeError("SHIT GOING DOWN DATABASE CORRUPTING")
        else:
            print("All is well in huntersville")


    # Test whether the backup can be restored
    with TemporaryDirectory() as temp_folder:

        restored_file = Path(temp_folder) / "restored_test.db"

        # Open the backup as our source
        with closing(sqlite3.connect(backup_file)) as source:

            # Open the temporary database as our destination
            with closing(sqlite3.connect(restored_file)) as destination:
                

                # Restore the backup into the temporary database
                source.backup(destination)

                with closing(sqlite3.connect(restored_file)) as verify_restored:

                    result = verify_restored.execute(

                        "SELECT COUNT(*) FROM practice_sessions"

                    ).fetchone()

                    session_count = result[0]

                    print(f"Restored {session_count} practice sessions!")

                    # Step 3: Confirm the restoration copy was created

                    print("Restoration copy created!")


if __name__ == "__main__":
    backup_database()