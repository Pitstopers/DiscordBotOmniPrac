import discord
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from typing import Literal
from contextlib import closing
import os

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

# Runs when the bot connects successfully
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    print("Slash Commands Synced!")

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
    await interaction.response.send_message(
        f"Check Practice logged\n"
        f"Player: {interaction.user.display_name}\n"
        f"Practice Type: {practice_type}\n"
        f"Duration: {hours}h {minutes}m\n"
        f"Total minutes: {total_minutes}\n"
    )
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO practice_sessions (user_id, username, practice_type, duration_minutes)
            VALUES (?, ?, ?, ?)
        """, (interaction.user.id, interaction.user.display_name, practice_type, total_minutes))

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
            (interaction.user.id,)
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
            SELECT practice_type, duration_minutes, created_at
            FROM practice_sessions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (interaction.user.id,)
        ).fetchall()

    if not records:
        await interaction.response.send_message("No Practice History Found.")
        return

    message = f"**Practice History: {interaction.user.display_name}**\n"

    for index, record in enumerate(records, start=1):
        practice_type, minutes, date = record

        message += (
            f"{index}. **{practice_type}**\n"
            f"Duration: {format_duration(minutes)}\n"
            f"Date: {date} UTC\n\n"
        )

    await interaction.response.send_message(message)

def format_duration(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

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

# Start the bot
bot.run(TOKEN)