import discord
import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the tokens from the .env file
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_BOTSPAM_CHANNEL_ID = int(os.getenv("DISCORD_BOTSPAM_CHANNEL_ID", "0"))
DISCORD_TRADE_CHANNEL_ID = int(os.getenv("DISCORD_TRADE_CHANNEL_ID", "0"))
FANTRAX_USERNAME = os.getenv("FANTRAX_USERNAME")
FANTRAX_PASSWORD = os.getenv("FANTRAX_PASSWORD")
FANTRAX_LEAGUE_ID = os.getenv("FANTRAX_LEAGUE_ID")

# Check if the token is found
if TOKEN is None:
    raise ValueError("No DISCORD_BOT_TOKEN found in .env file.")
if DISCORD_BOTSPAM_CHANNEL_ID is None:
    raise ValueError("No DISCORD_BOTSPAM_CHANNEL_ID found in .env file.")
if DISCORD_TRADE_CHANNEL_ID is None:
    raise ValueError("No DISCORD_TRADE_CHANNEL_ID found in .env file.")

# Check Fantrax credentials and set flag
FANTRAX_ENABLED = True
if not FANTRAX_USERNAME or not FANTRAX_PASSWORD or not FANTRAX_LEAGUE_ID:
    print("Warning: Missing Fantrax credentials. Fantrax integration will be disabled.")
    FANTRAX_ENABLED = False

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


# Tracked player

plus_minus_tracker = [
    {"name": "Tyler Myers", "id": 8474574}
]

shot_on_net_tracker = [
    {"name": "Cody Ceci", "id": 8476879}
]


test_players_to_track = [
    {"name": "Tyler Myers", "id": 8474574},
    {"name": "Elias Pettersson", "id": 8480012},
    {"name": "J.T. Miller", "id": 8476468},
    {"name": "Connor McDavid", "id": 8478402},
    {"name": "Alex Ovechkin", "id": 8471214},
    {"name": "Auston Matthews", "id": 8479318},
    {"name": "Nikita Zadorov", "id": 8477507},
    {"name": "Travis Sanheim", "id": 8477948},
    {"name": "Jack Eichel", "id": 8478403},
    {"name": "Jake Walman", "id": 8478013},
    {"name": "Darnell Nurse", "id": 8477498}
]

# API YEAR
NHL_YEAR = "20242025"

#FANTRAX

async def fantrax_login():
    if not FANTRAX_ENABLED:
        print("Fantrax integration is disabled, skipping Login.")
        return  # Exit early if Fantrax is disabled
     
    """Authenticate with Fantrax and return session token."""
    login_url = "https://www.fantrax.com/fxpa/req"
    
    payload = {
        "login": FANTRAX_USERNAME,
        "password": FANTRAX_PASSWORD,
        "method": "login"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, json=payload) as response:
            if response.status != 200:
                print("Error: Failed to authenticate with Fantrax.")
                return None
            
            data = await response.json()
            if "sessionId" in data:
                return data["sessionId"]
            else:
                print("Error: Fantrax login failed.")
                return None

async def track_fantrax_trades():
    """Track Fantrax trades and post them to Discord."""
    if not FANTRAX_ENABLED:
        print("Fantrax integration is disabled, skipping trade tracking.")
        return  # Exit early if Fantrax is disabled
    session_id = await fantrax_login()
    if not session_id:
        return

    league_id = os.getenv("FANTRAX_LEAGUE_ID")  # Store your league ID in .env
    last_trade_id = None

    channel = client.get_channel(DISCORD_TRADE_CHANNEL_ID)

    if channel is None:
        print("Error: Discord channel not found.")
        return

    while True:
        trades = await get_fantrax_trades(session_id, league_id)
        if trades:
            for trade in trades:
                trade_id = trade.get("tradeId")

                if trade_id != last_trade_id:  # Prevent duplicate messages
                    team_1 = trade["team1"]["name"]
                    team_2 = trade["team2"]["name"]
                    players_team_1 = ", ".join(player["name"] for player in trade["team1"]["players"])
                    players_team_2 = ", ".join(player["name"] for player in trade["team2"]["players"])

                    message = (
                        f"🔥 **New Trade Alert!** 🔥\n"
                        f"🏒 **{team_1}** traded: {players_team_1}\n"
                        f"🔄 **{team_2}** traded: {players_team_2}"
                    )

                    await channel.send(message)
                    last_trade_id = trade_id

        await asyncio.sleep(300)  # Check for new trades every 5 minutes


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

#Team functions 

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

#Tracking Functions 

async def track_player_events(player_id, channel, player_name):
    """Track a player's goals and goals against in real-time."""
    last_goals = None
    last_goals_against = None

    while True:
        try:
            NHL_PLAYER_STATS_URL = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={player_id} and seasonId={NHL_YEAR}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(NHL_PLAYER_STATS_URL) as response:
                    if response.status != 200:
                        logging.error(f"Error: Unable to fetch stats for {player_name} (ID: {player_id}). Status: {response.status}")
                        await asyncio.sleep(60)
                        continue

                    data = await response.json()
                    logging.info(f"API Response for {player_name} (ID: {player_id}): {data}")  # Debugging: Print the API response

                    if not data.get('data'):
                        logging.error(f"Error: No stats found for {player_name} (ID: {player_id}).")
                        await asyncio.sleep(60)
                        continue

                    player_stats = data['data'][0]
                    current_goals = player_stats.get('goals', 0)
                    current_goals_against = player_stats.get('plusMinus', 0)

                    if last_goals is None:
                        last_goals = current_goals
                    if last_goals_against is None:
                        last_goals_against = current_goals_against

                    if current_goals > last_goals:
                        await channel.send(f"🚨 {player_name} has scored a goal! Total goals: {current_goals}")
                        last_goals = current_goals

                    if current_goals_against < last_goals_against:
                        await channel.send(f"😬 {player_name} was on the ice for a goal against. Plus/Minus: {current_goals_against}")
                        last_goals_against = current_goals_against

                    print(f"No update for {player_id} {player_name} | Goals: {current_goals} | +/-: {current_goals_against}")
                    await asyncio.sleep(30)

        except Exception as e:
            logging.error(f"Error tracking player {player_name} (ID: {player_id}): {e}")
            await asyncio.sleep(60)

#Reading Functions 

@client.event
async def on_message(message):
    """Respond to the user's message with player stats."""
    if message.author == client.user:
        return

    # Convert the message content to lowercase for case-insensitive comparison
    content_lower = message.content.lower()

    if content_lower.startswith("!test"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID, DISCORD_TRADE_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return
        await message.channel.send("I am alive and listening!")

    if content_lower.startswith("!points"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("Usage: `!points <team_name>`")
            return

        team_name = parts[1]
        result = await get_team_points(team_name)
        await message.channel.send(result)

    if content_lower.startswith("!playerpoints"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("Usage: `!playerpoints <player_id_or_last_name>`")
            return

        player_input = parts[1]
        result = await get_player_points(player_input)
        await message.channel.send(result)

    # Shitpost messages
    if content_lower.startswith("!freepetey"):
        await message.channel.send("We will hold Petey hostage until our demands are met!")

@client.event
async def on_ready():
    """Start the bot and begin tracking player events."""
    print(f"Logged in as {client.user}")

    # Get the Discord channel where updates will be posted
    channel = client.get_channel(DISCORD_BOTSPAM_CHANNEL_ID)
    if channel is None:
        print("Error: botspam channel not found.")
        return

    # Start tracking all players
    for player in test_players_to_track:
        client.loop.create_task(track_player_events(player["id"], channel, player["name"]))

     # Start tracking Fantrax trades only if Fantrax is enabled
    if FANTRAX_ENABLED:
        client.loop.create_task(track_fantrax_trades())  # Start Fantrax trade tracking
    else:
        print("Fantrax integration is disabled.")

# Run the bot
client.run(TOKEN)
