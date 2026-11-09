import discord
import sqlite3
import asyncio
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
from pathlib import Path
from typing import Literal
from contextlib import closing
from sheets_sync import sync_practice_logs
from datetime import datetime, timezone
from discord import app_commands

# Find the .env file in the same folder as bot.py
env_file = Path(__file__).parent / ".env"

# Load the variables inside .env
load_dotenv(env_file)

# Read the Discord token
TOKEN = os.getenv("DISCORD_TOKEN")

DB_FILE = Path(__file__).parent / "practice_logs.db"

# Stop immediately if the token was not found
if TOKEN is None:
    raise ValueError("DISCORD_TOKEN could not be found in .env")

# Default Discord intents
intents = discord.Intents.default()

# Create the bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

def setup_database():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS practice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                practice_type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS active_stopwatches (
                user_id INTEGAR PRIMARY KEY,
                username TEXT NOT NULL,
                practice_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
                )
        """)
        columns = [
            column[1]
            for column in conn.execute(
                "PRAGMA table_info(active_stopwatches)"
            ).fetchall()
        ]
        if "last_reminded_at" not in columns:
            conn.execute(
                """
                ALTER TABLE active_stopwatches
                ADD COLUMN last_reminded_at TEXT
            """)

@tasks.loop(seconds=15)
async def stopwatch_reminder_checker():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
                records = conn.execute(
                    """
                    SELECT user_id, started_at, last_reminded_at
                    FROM active_stopwatches
                """
                ).fetchall()

        for record in records:
            user_id, started_at_text, last_reminded_at = record
            started_at = datetime.fromisoformat(started_at_text)

            current_time = datetime.now(timezone.utc)
            elasped = current_time - started_at
            elasped_minutes = int(elasped.total_seconds() //60 )
            if elasped_minutes >= 1:
                print(user_id, "needs a stopwatch notication")

# Runs when the bot connects successfully
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    print("Slash Commands Synced!")
    if not stopwatch_reminder_checker.is_running():
        stopwatch_reminder_checker.start()

@bot.tree.command(
    name="ping",
    description="Check if the bot is alive"
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(
    name="practice",
    description="Log Prac time",
)
async def practice(
    interaction: discord.Interaction,
    hours: int,
    minutes: int,
    practice_type: Literal[
        "Ranked",
        "Practice",
        "1v1s",
        "Solo",
        ],
    notes: str = ""
):
    if hours < 0:
        await interaction.response.send_message("Hours cannot be negative.",
        ephemeral=True)
        return
    if minutes < 0 or minutes >= 60:
        await interaction.response.send_message("Minutes must be between 0 and 59.",
        ephemeral=True)
        return
    if hours == 0 and minutes == 0:
        await interaction.response.send_message("Practice duration cannot be zero.",
        ephemeral=True)
        return

    # Calculate total practice duration
    total_minutes = (hours * 60) + minutes

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            """
            INSERT INTO practice_sessions 
            (user_id, username, practice_type, duration_minutes, session_details, interaction_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(interaction_id) DO NOTHING;
        """,
            (
                interaction.user.id, 
                interaction.user.display_name, 
                practice_type,
                total_minutes,
                str(notes),
                str(interaction.id)
            )
        )
        inserted_count = cursor.rowcount
        session_id = cursor.lastrowid

    if inserted_count == 0:
        await interaction.response.send_message(
            "Practice already recorded!",
            ephemeral=True
        )
        return

    
    await interaction.response.send_message(
        f"**Session ID: {session_id}**\n\n"
        f"Check Practice logged\n"
        f"Player: {interaction.user.display_name}\n"
        f"Practice Type: {practice_type}\n"
        f"Duration: {hours}h {minutes}m\n"
        f"Total minutes: {total_minutes}\n\n"
        f"**Notes: {notes.strip() or 'NONE**'}"
    )
    
    await update_google_sheets()


@bot.tree.command(
    name="stats",
    description="TBA"
)
async def stats(interaction: discord.Interaction):

    with closing(sqlite3.connect(DB_FILE)) as conn:
        result = conn.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(duration_minutes), 0)
            FROM practice_sessions
            WHERE user_id = ?
            """,
            (interaction.user.id, )
        ).fetchone()

        sessions, total_minutes = result

        if sessions == 0:
            await interaction.response.send_message(
                "You haven't logged any practice sessions yet."
            )
            return


        await interaction.response.send_message(
        f"**Practice Stats: {interaction.user.display_name}**\n"
        f"Total Sessions: {sessions}\n"
            f"Total Practice: {format_duration(total_minutes)}"
        )

@bot.tree.command(
    name="history",
    description="TBA"
 )
async def history(interaction: discord.Interaction):

    with closing(sqlite3.connect(DB_FILE)) as conn:
        records = conn.execute(
            """
            Select id,practice_type, duration_minutes, created_at
            FROM practice_sessions
            WHERE user_id =?
            ORDER BY id DESC
            LIMIT 5
            """,
            (interaction.user.id,)
        ).fetchall()
    
        if not records:
             await interaction.response.send_message(
                 "No Practice History Found."
             )
             return
             
    message = f"**Practice History: {interaction.user.display_name}**\n"

    for index, record in enumerate(records, start=1):
                session_id, practice_type, total_minutes, date = record

                message += (
                    f"{index}. **Session #{session_id} - {practice_type}**\n"
                    f"Duration: {format_duration(total_minutes)}\n"
                    f"Date: {date} UTC\n\n"
                )

    await interaction.response.send_message(message)

def format_duration(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

class PartnerSelector(discord.ui.view.View):

    def __init__(self, session_id, owner_id):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.session_id = session_id
        self.owner_id = owner_id
        self.selected_partners = []
    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select practice partners...",
        min_values=1,
        max_values=10
    )
    async def choose_partners(
        self,
        interation: discord.Interaction,
        select: discord.ui.UserSelect
    ):
        if interation.user.id != self.owner_id:
            await interation.response.send_message(
                "You are not authorized to select partners for this session.",
                ephemeral=True
            )
            return

        partner_ids = [
            str(user.id)
            for user in select.values
            if user.id != self.owner_id
        ]

        if not partner_ids:
            await interation.response.send_message(
                "You cannot select yourself as a partner.",
                ephemeral=True
            )
            return
        with closing(sqlite3.connect(DB_FILE)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
                        
            with conn:
                # Check if the 'practice_partners' table exists
                session = conn.execute(
                """
                SELECT id from practice_sessions
                WHERE id = ? AND user_id = ?
                """,
                (self.session_id, self.owner_id)
                ).fetchone()

                if session is None:
                    await interation.response.send_message(
                        "The practice session no longer exists or you are not the owner.",
                        ephemeral=True
                    )
                    return

                conn.execute(
                    "DELETE FROM practice_partners WHERE session_id = ?",
                    (self.session_id,)
                )

                conn.executemany(
                    """
                    INSERT INTO practice_partners 
                    (session_id, partner_user_id)
                    VALUES (?, ?)
                    """,
                    [   
                        (self.session_id, partner_id) 
                        for partner_id in partner_ids
                    ]
                )

                await interation.response.send_message(
                    f"Saved {len(partner_ids)} practice partners "
                    f"for session #{self.session_id}!",
                    ephemeral=True
                )
@bot.tree.command(
    name="leaderboard",
    description="View the practice leaderboard"
)
async def leaderboard(interaction: discord.Interaction):

    with closing(sqlite3.connect(DB_FILE)) as conn:
        records = conn.execute(
            """
            SELECT 
                latest.username,
                totals.total_minutes,
                totals.sessions
                FROM (
                    SELECT
                        user_id, 
                        SUM(duration_minutes) AS total_minutes,
                        COUNT(*) AS sessions,
                        MAX(id) AS latest_id
                    FROM practice_sessions
                    GROUP BY user_id
                ) AS totals
                JOIN practice_sessions AS latest
                    ON latest.id = totals.latest_id
                ORDER BY totals.total_minutes DESC
                LIMIT 10
            """
        ).fetchall()

    if not records:
        await interaction.response.send_message(
            "No players have logged practice yet."
        )
        return

    message = "**OMNI Practice Leaderboard**\n\n"

    for rank, record in enumerate(records, start=1):
        username, minutes, sessions = record
       
        message += (
            f"**#{rank} {username}**\n"
            f"Practice: {format_duration(minutes)}\n"
            f"Sessions: {sessions}\n\n"
        )

    await interaction.response.send_message(message)

@bot.tree.command(
    name="deletepractice",
    description="Delete a practice session by its ID"
)
async def delete(interaction: discord.Interaction, session_id: int):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
            result = conn.execute(
                """
                DELETE FROM practice_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, interaction.user.id)
            )

            deleted_rows = result.rowcount

            if deleted_rows == 0:
                await interaction.response.send_message(
                    f"No practice session found with ID {session_id} for your account.",
                    ephemeral=True
                )
                return

    await interaction.response.send_message(
        f"Practice session with ID {session_id} has been deleted.",
        ephemeral=True
    )
    await update_google_sheets()

@bot.tree.command(
    name="editpractice",
    description="Edit a practice session by its ID"
)
async def edit(
        interaction: discord.Interaction, 
        session_id: int, 
        hours: int, 
        minutes: int, 
        practice_type: Literal[
            "Ranked", 
            "Practice", 
            "1v1s", 
            "Solo"
            ]
    ):
        if hours < 0:
            await interaction.response.send_message("Hours cannot be negative.",
            ephemeral=True)
            return
        if minutes < 0 or minutes >= 60:
            await interaction.response.send_message("Minutes must be between 0 and 59.",
            ephemeral=True)
            return
        if hours == 0 and minutes == 0:
            await interaction.response.send_message("Practice duration cannot be zero.",
            ephemeral=True)
            return

        total_minutes = (hours * 60) + minutes

        with closing(sqlite3.connect(DB_FILE)) as conn:
            with conn:
                result = conn.execute(
                    """
                    UPDATE practice_sessions
                    SET duration_minutes = ?,
                        practice_type = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (
                        total_minutes, 
                        practice_type, 
                        session_id, 
                        interaction.user.id
                    )
                )

                updated_rows = result.rowcount

                if updated_rows == 0:
                    await interaction.response.send_message(
                        f"No practice session found with ID {session_id} for your account.",
                        ephemeral=True
                    )
                    return

        await interaction.response.send_message(
            f"Practice session with ID {session_id} has been updated to {practice_type} for {hours}h {minutes}m.",
            ephemeral=True
        )
        await update_google_sheets()

stopwatch_group = app_commands.Group(
        name="stopwatch",
        description="StopWatch your practice"
)
@stopwatch_group.command(
    name="start",
    description="Start tracking your practice time"
)
async def stopwatch_start(
    interaction: discord.Interaction,
    practice_type: Literal[
        "Ranked",
        "Practice",
        "1v1s",
        "Solo",
        ],
    notes: str = ""
):

    started_at = datetime.now(timezone.utc)
    unix_timestamp = int(started_at.timestamp())
    started_at_text = started_at.isoformat()

    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO active_stopwatches
                (user_id, username, practice_type, started_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """,
            (
                interaction.user.id,
                interaction.user.display_name,
                practice_type,
                started_at_text,
                notes.strip()
            )
        )
        inserted_count = cursor.rowcount

    if inserted_count == 0:
        await interaction.response.send_message(
            "Stopwatch already started!",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
    f"**OMNI GALAXY STOPWATCH**\n"
    f"**Practice Started!**\n\n"
    f"**Started:** <t:{unix_timestamp}:t>\n"
    f"**Mode:** {practice_type}\n"
    f"**Notes:** {notes.strip() or 'None'}",
    ephemeral=True
    )

@stopwatch_group.command(
    name="stop",
    description="Stop and save your practice"
)
async def stopwatch_stop(interaction: discord.Interaction):
    record = None
    elasped_minutes = None
    session_id = None

    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            
            record = conn.execute(
                """
                SELECT practice_type, started_at, notes
                FROM active_stopwatches
                WHERE user_id = ?
                """,
                (interaction.user.id,)
            ).fetchone()

            if record is not None:
                practice_type, started_at_text, notes = record

                started_at = datetime.fromisoformat(started_at_text)
                stopped_at = datetime.now(timezone.utc)
                unix_timestamp = int(started_at.timestamp())

                elasped = stopped_at - started_at
                elasped_minutes = int(elasped.total_seconds() // 60)

                if elasped_minutes >= 1:
                    cursor = conn.execute(
                    """
                    INSERT INTO practice_sessions
                    (user_id, username, practice_type, duration_minutes, session_details, interaction_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interaction.user.id,
                        interaction.user.display_name,
                        practice_type,
                        elasped_minutes,
                        notes,
                        str(interaction.id)
                    )
                )
                    
                    session_id = cursor.lastrowid
                    conn.execute(
                        """
                        DELETE FROM active_stopwatches
                        WHERE user_id = ?
                        """,
                        (interaction.user.id,)
                    )

    if record is None:
        await interaction.response.send_message(
            "You don't have an active stopwatch.",
            ephemeral=True
        )
        return
    
    if elasped_minutes < 1:
        await interaction.response.send_message(
            "your stopwatch hasn't reached one minute yet",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
    f"**OMNI GALAXY STOPWATCH**\n"
    f"**Session ID: {session_id}**\n"
    f"**Started:** <t:{unix_timestamp}:t>\n"
    f"**No longer active!**\n\n"
    f"**Mode:** {practice_type}\n"
    f"**Duration** {format_duration(elasped_minutes)}\n"
    f"**Notes:** {notes.strip() or 'None'}",
    ephemeral=True
    )
    await update_google_sheets()
bot.tree.add_command(stopwatch_group)

@bot.tree.command(
    name="addpartners",
    description="Add practice partners to a session"
)
async def add_partners(
    interaction: discord.Integration,
    session_id: int
):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        session = conn.execute(
            """
            SELECT id
            FROM practice_sessions
            WHERE id = ? AND user_id = ?
            """,
            (session_id, interaction.user.id)
        ).fetchone()

        if session is None:
            await interaction.response.send_message(
                f"No practice session found with ID {session_id}.",
                ephemeral=True
            )
            return

    view = PartnerSelector(
        session_id=session_id,
        owner_id=interaction.user.id
    )

    await interaction.response.send_message(
        f"Select your practice partners from the dropdown below:",
        view=view,
        ephemeral=True
    )
    print("Dropdown components:", view.children)
    await update_google_sheets()

# Setup the database when the bot starts
setup_database()

sheets_sync_lock = asyncio.Lock()

async def update_google_sheets():
        async with sheets_sync_lock:
            try:
                await asyncio.to_thread(sync_practice_logs)
                print("Practice logs synced to Google Sheets successfully.")
            except Exception as error:
                print(f"Error syncing practice logs to Google Sheets: {error}")

@bot.tree.command(
        name="addnotes",
        description="Add notes from your practice session"
)
async def add_notes(
    interaction: discord.Interaction,
    session_id: int,
    notes: str
):
    if not notes.strip():
        await interaction.response.send_message(
            f"Practice notes connot be empty",
            ephemeral=True
        )
        return
    
    with closing(sqlite3.connect(DB_FILE)) as conn:
        session = conn.execute(
            """
            SELECT id
            FROM practice_sessions
            WHERE id = ? AND user_id = ?
            """,
            (session_id, interaction.user.id)
        ).fetchone()

        if session is None:
            await interaction.response.send_message(
                f"No practice session found with ID {session_id}.",
                ephemeral=True
            )
            return
        with conn:
            conn.execute(
                """
                UPDATE practice_sessions
                SET session_details = ?
                WHERE id = ? AND user_id = ?
                """,
                (notes, session_id, interaction.user.id)
            )

    await interaction.response.send_message(
        f"Practice notes saved for session #{session_id}!\n"
        f"Your notes are: **{notes}**",
        ephemeral=True
    )
    await update_google_sheets()

@bot.tree.command(
    name="commands",
    description="See all Practice Tracker commands"
)
async def show_commands(interaction: discord.Interaction):
    available_commands = sorted(
        bot.tree.get_commands(),
        key=lambda cmd: cmd.name
    )

    command_list = []

    for command in available_commands:
        command_list.append(
            f"/{command.name} - {command.description}"
        )
        embed = discord.Embed(
            title="OMNI Practice Tracker Commands",
            description="\n".join(command_list),
            color=discord.Color.blurple()
        )
        embed.set_footer(
            text="Need help getting started? Use /tutorial"
        )
        await interaction.response.send_message(
            embed=embed, 
            ephemeral=True
            )

@bot.tree.command(
    name="tutorial",
    description="Learn how to use OMNI Practice Tracker"
)
async def tutorial(interaction: discord.Interaction):

    embed = discord.Embed(
        title="OMNI Practice Tracker — Tutorial",
        description="Follow these steps to get started!",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Step 1 — Log your practice",
        value="Use `/practice` to record your practice type and duration.",
        inline=False
    )

    embed.add_field(
        name="Step 2 — Find your session",
        value="Use `/history` to see your previous sessions and their IDs.",
        inline=False
    )

    embed.add_field(
        name="Step 3 — Add practice partners",
        value=(
            "Use `/addpartners` with your session ID, then select the people you practiced with.\n"
            "**NOTE:** Tagging a practice partner doesn't automatically give that partner logged practice time. They must log their own practice separately."
        ),
        inline=False
    )

    embed.add_field(
        name="Step 4 — Review your progress",
        value="Use `/stats` for your statistics or `/leaderboard` to compare practice totals.",
        inline=False
    )

    embed.add_field(
        name="Step 5 — Correct a mistake",
        value="Use `/editpractice` to update a session or `/deletepractice` to remove one.",
        inline=False
    )

    embed.set_footer(
        text="Practice Tracker"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )

# Start the bot
bot.run(TOKEN)