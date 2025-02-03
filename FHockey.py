import discord
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the token from the .env file
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Check if the token is found
if TOKEN is None:
    raise ValueError("No DISCORD_BOT_TOKEN found in .env file.")

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True  # Allow reading messages
intents.guilds = True
intents.message_content = True  # Required to read message content

client = discord.Client(intents=intents)

# NHL API Endpoints
NHL_STATS_URL = "https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={}"
NHL_PLAYER_INFO_URL = "https://api-web.nhle.com/v1/player/{}/landing"

# Player and team tracking
TRACKED_PLAYER_ID = 8475166  # Example Player (Tyler Myers)
DISCORD_CHANNEL_ID = 1016200685626335242  # Your Discord channel ID

# Store last event ID to prevent duplicate messages
last_event_id = None

async def get_player_info(player_id):
    """Fetch player info to verify if the player exists and return their full name."""
    url = NHL_PLAYER_INFO_URL.format(player_id)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None  # Player not found
            
            data = await response.json()

            # Fix: Extract player name properly from JSON structure
            try:
                player_name = data['fullName']  # Correct key for player name
                return player_name
            except KeyError:
                return None  # If fullName is missing, return None
            

async def get_team_points(team_name):
    """Fetch the current season points for a given NHL team."""
    
    # NHL API endpoint for team standings
    NHL_TEAM_STANDINGS_URL = "https://api-web.nhle.com/v1/standings/now"

    async with aiohttp.ClientSession() as session:
        async with session.get(NHL_TEAM_STANDINGS_URL) as response:
            if response.status != 200:
                return "Error: Unable to fetch team standings."

            data = await response.json()

            # Loop through the teams to find a match
            for team in data["standings"]:
                # Extract team names and abbreviation
                team_name_english = team.get("teamName", {}).get("default", "Unknown Team")
                team_name_french = team.get("teamName", {}).get("fr", "Unknown Team")
                team_abbrev = team.get("teamAbbrev", {}).get("default", "Unknown Team")

                # Check if the user's input matches any of the team's names or abbreviation
                if (team_name.lower() in team_name_english.lower() or
                    team_name.lower() in team_name_french.lower() or
                    team_name.lower() == team_abbrev.lower()):
                    team_points = team["points"]
                    return f"🏒 {team_name_english} currently has {team_points} points this season!"

            return f"Error: Team '{team_name}' not found. Please check you spelling"




async def get_player_stats(player_id):
    """Fetch player goals from the NHL API."""
    
    # First, check if the player exists
    player_name = await get_player_info(player_id)
    if not player_name:
        return f"Error: Player ID {player_id} not found in the NHL database."

    # Now, fetch the player's stats
    url = NHL_STATS_URL.format(player_id)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return "Error: Unable to fetch stats."

            data = await response.json()

            # Check if stats exist
            if not data['data']:
                return f"🏒 {player_name} has not recorded any stats this season."

            try:
                player_stats = data['data'][0]
                goals = player_stats.get('goals', 0)  # Default to 0 if missing
                return f"🏒 {player_name} has scored {goals} goals this season!"
            except KeyError:
                return "Error: Could not retrieve goal stats."

@client.event
async def on_message(message):
    """Respond to the user's message with player stats."""
    if message.author == client.user:
        return

    if message.content.startswith("!test"):
        await message.channel.send("I am alive and listening!")

    if message.content.startswith("!points"):
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("Usage: `!points <team_name>`")
            return

        team_name = parts[1]
        result = await get_team_points(team_name)
        await message.channel.send(result)

    if message.content.startswith("!goals"):
        parts = message.content.split()
        if len(parts) != 2:
            await message.channel.send("Usage: `!goals <player_id>`")
            return

        try:
            player_id = int(parts[1])
        except ValueError:
            await message.channel.send("Invalid player ID. Please enter a valid number.")
            return

        result = await get_player_stats(player_id)
        await message.channel.send(result)

# Run the bot
client.run(TOKEN)
