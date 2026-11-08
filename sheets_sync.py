import os
import sqlite3
from pathlib import Path
from contextlib import closing

import gspread
from dotenv import load_dotenv

Base_DIR = Path(__file__).parent

load_dotenv(Base_DIR / ".env")

DB_FILE = Base_DIR / "practice_logs.db"
SHEET_ID = os.environ["GOOGLE_SHEETS_ID"]

def format_minutes(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"
    
def sync_practice_logs():

    with closing(sqlite3.connect(DB_FILE)) as conn:
        records = conn.execute(
            """
            SELECT 
                id, 
                user_id, 
                username, 
                practice_type, 
                duration_minutes, 
                created_at
            FROM practice_sessions
            ORDER BY id ASC
            """
        ).fetchall()

        partner_links = conn.execute(
            """
            SELECT
                s.id,
                p.partner_user_id
            FROM practice_sessions AS s
            LEFT JOIN practice_partners AS p
                ON s.id = p.session_id
                ORDER BY s.id
            """
        ).fetchall()

        known_usernames = {}

        usernames_records = conn.execute("""
            SELECT user_id, username
            FROM practice_sessions
            WHERE username IS NOT NULL
                AND username != ''
            ORDER BY id DESC
        """).fetchall()

        for user_id, username in usernames_records:
            known_usernames.setdefault(
                str(user_id),
                username
            )

        partners_by_session = {}

        for session_id, partner_id in partner_links:
            if session_id not in partners_by_session:
                partners_by_session[session_id] = []

            if partner_id is not None:
                partners_by_session[session_id].append(
                    str(partner_id)
                )

                print("Practice partner records:", partners_by_session)

        print(f"Found {len(records)} practice sessions.")
        rows = [[
            "Session ID", 
            "Discord User ID", 
            "Player Name", 
            "Practice Type", 
            "Duration (minutes)", 
            "Duration Hours",
            "Recorded At (UTC)",
            "Practice Partners"
        ]]

        for record in records:
            session_id, user_id, username, practice_type, minutes, date = record

            hours = round(minutes / 60, 2)

            
            partner_names = []

            for partner_id in partners_by_session.get(session_id, []):
                partner_username = known_usernames.get(partner_id)

                if partner_username:
                    partner_names.append(
                        f"{partner_username} ({partner_id})"
                    )
                else:
                    partner_names.append(partner_id)

            partner_text = ", ".join(partner_names)

            rows.append([
                session_id,
                str(user_id),
                username,
                practice_type,
                minutes,
                hours,
                date,
                partner_text
            ])

        # All practice session rows have now been created
        for row in rows:
            print(row)

        expected_rows = len(records) + 1

        if len(rows) != expected_rows:
            raise ValueError(
                f"Expected {expected_rows} rows, "
                f"but generated {len(rows)}."
            )

        for row_number, row in enumerate(rows, start=1):
            if len(row) != 8:
                raise ValueError(
                    f"Row {row_number} has {len(row)} columns. "
                    "Expected 8."
                )

        print("Data validation passed!")

        # Connect to Google Sheets
        client = gspread.service_account(
        filename=Base_DIR / "google-service-account.json"
        )

        spreadsheet = client.open_by_key(SHEET_ID)
        print(f"Connected to spreadsheet: {spreadsheet.title}")
        worksheet = spreadsheet.worksheet("Practice Logs")

        existing_count = len(worksheet.get_all_values())
        row_count = max(existing_count, len(rows))

        rows += [[""] * 8 for _ in range(row_count - len(rows))]

        worksheet.update(
            values=rows,
            range_name=f"A1:H{row_count}",
            value_input_option="RAW"
        )

        worksheet.freeze(rows=1)

        worksheet.set_basic_filter(f"A1:H{expected_rows}")
        
        print("Practice logs synced to Google Sheets successfully.")

        print("DEBUG: Starting Player summary")
        sync_player_summary(records, spreadsheet)
        print("DEBUG Finished syncing player summary")

def sync_player_summary(records, spreadsheet):
    print("DEBUG 3: Player Summary function started")
    print(f"Processing {len(records)} records")

    players = {}

    # Group all practice records by Discord User ID
    for record in records:
        session_id, user_id, username, practice_type, minutes, date = record

        user_id = str(user_id)

        if user_id not in players:
            players[user_id] = {
                "username": username,
                "total_minutes": 0,
                "sessions": 0,
                "types": {}
            }

        # Update this player for EVERY session
        player = players[user_id]

        player["username"] = username
        player["total_minutes"] += minutes
        player["sessions"] += 1

        if practice_type not in player["types"]:
            player["types"][practice_type] = {
                "minutes": 0,
                "sessions": 0
            }

        player["types"][practice_type]["minutes"] += minutes
        player["types"][practice_type]["sessions"] += 1

    # Build the summary AFTER processing all records
    summary_rows = [
        ["OMNI - Player Summary", "", "", ""],
        ["Grouped By Discord User ID", "", "", ""],
        ["", "", "", ""]
    ]

    sorted_players = sorted(
        players.items(),
        key=lambda x: x[1]["total_minutes"],
        reverse=True
    )

    # Generate one section for each player
    for user_id, player in sorted_players:

        summary_rows.append([
            player["username"],
            "",
            "Discord User ID",
            user_id
        ])

        summary_rows.append([
            "Total Practice",
            format_minutes(player["total_minutes"]),
            "Total Sessions",
            player["sessions"]
        ])

        summary_rows.append([
            "Practice Type", "Total Time", "Sessions", ""
        ])

        for practice_type, data in sorted(player["types"].items()):
            summary_rows.append([
                practice_type,
                format_minutes(data["minutes"]),
                data["sessions"],
                ""
            ])

        summary_rows.append(["", "", "", ""])

    # Upload the complete summary to Google Sheets
    worksheet = spreadsheet.worksheet("Player Summary")

    existing_count = len(worksheet.get_all_values())
    row_count = max(existing_count, len(summary_rows))

    summary_rows += [
        [""] * 4
        for _ in range(row_count - len(summary_rows))
    ]

    worksheet.update(
        values=summary_rows,
        range_name=f"A1:D{row_count}",
        value_input_option="RAW"
    )

    print("Player Summary synced successfully!")

if __name__ == "__main__":
    sync_practice_logs()