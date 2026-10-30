import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import os

# Find the .env file in the same folder as bot.py
env_file = Path(__file__).parent / ".env"

# Load the variables inside .env
load_dotenv(env_file)

# Read the Discord token
TOKEN = os.getenv("DISCORD_TOKEN")

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
    minutes: int
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
        f"Duration: {hours}h {minutes}m\n"
        f"Total minutes: {total_minutes}\n"
    )
# Start the bot
bot.run(TOKEN)