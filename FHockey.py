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
NHL_PLAYER_SEARCH_URL = "https://api-web.nhle.com/v1/search/player?q={}"

# Player and team tracking
TRACKED_PLAYER_ID = 8475166  # Example Player (Tyler Myers)
DISCORD_CHANNEL_ID = 1016200685626335242  # Your Discord channel ID

# API YEAR
NHL_YEAR = "20242025"

# Store last event ID to prevent duplicate messages
last_event_id = None

async def get_player_info(player_id):
    """Fetch player info to verify if the player exists and return their full name."""
    url = NHL_PLAYER_INFO_URL.format(player_id)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Error: Unable to fetch player info for ID {player_id}. Status: {response.status}")
                return None  # Player not found
            
            data = await response.json()
            print("Player Info API Response:", data)  # Debugging: Print the API response

            # Extract player name from firstName and lastName
            try:
                first_name = data['firstName']['default']
                last_name = data['lastName']['default']
                full_name = f"{first_name} {last_name}"
                return full_name
            except KeyError:
                print(f"Error: 'firstName' or 'lastName' not found in API response for ID {player_id}.")
                return None  # If firstName or lastName is missing, return None

async def search_players_by_last_name(last_name):
    """Search for players by last name and return a list of matching players."""
    url = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=lastName likeIgnoreCase '{last_name}%'"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return "Error: Unable to search for players."

            data = await response.json()
            print("API Response:", data)  # Debugging: Print the entire API response

            # Extract player information and remove duplicates
            players = []
            seen_player_ids = set()  # Track unique player IDs
            for player in data.get("data", []):  # Player data is under the "data" key
                player_id = player.get("playerId")
                full_name = player.get("skaterFullName", "Unknown Player")
                if player_id and full_name and player_id not in seen_player_ids:  # Ensure unique players
                    players.append((player_id, full_name))
                    seen_player_ids.add(player_id)  # Mark this player ID as seen

            if not players:
                return "Error: No players found in the API response."

            return players



async def get_player_points(player_input):
    """Fetch a player's total points (goals + assists) from the NHL API."""
    
    # Check if the input is a player ID (numeric)
    if player_input.isdigit():
        player_id = int(player_input)
        player_name = await get_player_info(player_id)
        if not player_name:
            return f"Error: Player ID {player_id} not found."

        # Fetch player stats for all seasons
        NHL_PLAYER_STATS_URL = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={player_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(NHL_PLAYER_STATS_URL) as response:
                if response.status != 200:
                    return "Error: Unable to fetch player stats."

                data = await response.json()

                # Check if stats exist
                if not data['data']:
                    return f"🏒 {player_name} has not recorded any stats this season."

                # Filter stats for the current season
                current_season = "20242025"  # Update this for the current season
                current_season_stats = None
                for stats in data['data']:
                    if stats['seasonId'] == int(current_season):
                        current_season_stats = stats
                        break

                if not current_season_stats:
                    return f"🏒 {player_name} has not recorded any stats this season."

                try:
                    goals = current_season_stats.get('goals', 0)  # Default to 0 if missing
                    assists = current_season_stats.get('assists', 0)  # Default to 0 if missing
                    points = goals + assists
                    return f"🏒 {player_name} has {points} points ({goals} goals + {assists} assists) this season!"
                except KeyError:
                    return "Error: Could not retrieve player stats."

    # If the input is a last name, search for matching players
    else:
        players = await search_players_by_last_name(player_input)
        if isinstance(players, str):  # If an error message is returned
            return players

        # If multiple players are found, list them all
        if len(players) > 1:
            response = "Multiple players found. Please specify by ID:\n"
            for player_id, full_name in players:
                response += f"- {full_name} (ID: {player_id})\n"
            return response

        # If only one player is found, fetch their points
        else:
            player_id, player_name = players[0]
            NHL_PLAYER_STATS_URL = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={player_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(NHL_PLAYER_STATS_URL) as response:
                    if response.status != 200:
                        return "Error: Unable to fetch player stats."

                    data = await response.json()

                    # Check if stats exist
                    if not data['data']:
                        return f"🏒 {player_name} has not recorded any stats this season."

                    # Filter stats for the current season
                    current_season = NHL_YEAR  # Update this for the current season
                    current_season_stats = None
                    for stats in data['data']:
                        if stats['seasonId'] == int(current_season):
                            current_season_stats = stats
                            break

                    if not current_season_stats:
                        return f"🏒 {player_name} has not recorded any stats this season."

                    try:
                        goals = current_season_stats.get('goals', 0)  # Default to 0 if missing
                        assists = current_season_stats.get('assists', 0)  # Default to 0 if missing
                        points = goals + assists
                        return f"🏒 {player_name} has {points} points ({goals} goals + {assists} assists) this season!"
                    except KeyError:
                        return "Error: Could not retrieve player stats."
#team functions 

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

#reading Functions 

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

    if message.content.startswith("!playerpoints"):
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("Usage: `!playerpoints <player_id_or_last_name>`")
            return

        player_input = parts[1]
        result = await get_player_points(player_input)
        await message.channel.send(result)

# Run the bot
client.run(TOKEN)
