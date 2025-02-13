import discord
import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # Import BeautifulSoup for scraping
import requests  # Import requests for HTTP requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

VERSION = "0.3.5"

# Load environment variables from .env file
load_dotenv()

# Get the tokens from the .env file
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_BOTSPAM_CHANNEL_ID = int(os.getenv("DISCORD_BOTSPAM_CHANNEL_ID", "0"))
DISCORD_TRADE_CHANNEL_ID = int(os.getenv("DISCORD_TRADE_CHANNEL_ID", "0"))
DISCORD_INFO_CHANNEL_ID = int(os.getenv("DISCORD_INFO_CHANNEL_ID", "0"))
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
if DISCORD_INFO_CHANNEL_ID is None:
    raise ValueError("No DISCORD_INFO_CHANNEL_ID found in .env file.")

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


ADMIN_OVERRIDE = False  # Set this to True to allow add/delete channel commands

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
    {"name": "Darnell Nurse", "id": 8477498},
    {"name": "Zach Werenski", "id": 8478460}
]

#team name dictionary
TEAM_NAME_TO_ABBREVIATION = {
    "Anaheim Ducks": "ANA", "Ducks d'Anaheim": "ANA",
    "Arizona Coyotes": "ARI", "Coyotes de l'Arizona": "ARI",
    "Boston Bruins": "BOS", "Bruins de Boston": "BOS",
    "Buffalo Sabres": "BUF", "Sabres de Buffalo": "BUF",
    "Calgary Flames": "CGY", "Flames de Calgary": "CGY",
    "Carolina Hurricanes": "CAR", "Hurricanes de la Caroline": "CAR",
    "Chicago Blackhawks": "CHI", "Blackhawks de Chicago": "CHI",
    "Colorado Avalanche": "COL", "Avalanche du Colorado": "COL",
    "Columbus Blue Jackets": "CBJ", "Blue Jackets de Columbus": "CBJ",
    "Dallas Stars": "DAL", "Stars de Dallas": "DAL",
    "Detroit Red Wings": "DET", "Red Wings de Détroit": "DET",
    "Edmonton Oilers": "EDM", "Oilers d'Edmonton": "EDM",
    "Florida Panthers": "FLA", "Panthers de la Floride": "FLA",
    "Los Angeles Kings": "LAK", "Kings de Los Angeles": "LAK",
    "Minnesota Wild": "MIN", "Wild du Minnesota": "MIN",
    "Montreal Canadiens": "MTL", "Canadiens de Montréal": "MTL",
    "Nashville Predators": "NSH", "Predators de Nashville": "NSH",
    "New Jersey Devils": "NJD", "Devils du New Jersey": "NJD",
    "New York Islanders": "NYI", "Islanders de New York": "NYI",
    "New York Rangers": "NYR", "Rangers de New York": "NYR",
    "Ottawa Senators": "OTT", "Senateurs d'Ottawa": "OTT",
    "Philadelphia Flyers": "PHI", "Flyers de Philadelphie": "PHI",
    "Pittsburgh Penguins": "PIT", "Penguins de Pittsburgh": "PIT",
    "San Jose Sharks": "SJS", "Sharks de San Jose": "SJS",
    "Seattle Kraken": "SEA", "Kraken de Seattle": "SEA",
    "St. Louis Blues": "STL", "Blues de Saint-Louis": "STL",
    "Tampa Bay Lightning": "TBL", "Lightning de Tampa Bay": "TBL",
    "Toronto Maple Leafs": "TOR", "Maple Leafs de Toronto": "TOR",
    "Vancouver Canucks": "VAN", "Canucks de Vancouver": "VAN",
    "Vegas Golden Knights": "VGK", "Golden Knights de Vegas": "VGK",
    "Washington Capitals": "WSH", "Capitals de Washington": "WSH",
    "Winnipeg Jets": "WPG", "Jets de Winnipeg": "WPG",
}

# API YEAR
def get_current_season():
    """Dynamically determine the current NHL season."""
    now = datetime.now()
    year = now.year
    if now.month < 7:  # NHL season starts in October and ends around June
        return f"{year - 1}{year}"
    return f"{year}{year + 1}"

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

#WEBSCRAPE
# Input Handler
def convert_team_name_to_abbreviation(team_name: str):
    """Convert full team name (English/French) to team abbreviation.
       If an abbreviation is provided, validate and return it."""
    team_name = team_name.strip().lower()
    
    # Create a set of valid abbreviations for quick lookup
    valid_abbreviations = set(TEAM_NAME_TO_ABBREVIATION.values())

    # Check if the input is already a valid abbreviation
    if team_name.upper() in valid_abbreviations:
        print(f"Valid abbreviation: {team_name.upper()}")
        return team_name.upper()
    
    # Check for full team names
    for full_name, abbreviation in TEAM_NAME_TO_ABBREVIATION.items():
        if team_name == full_name.lower():
            print(f"Team Name: {full_name} -> Abbreviation: {abbreviation}")
            return abbreviation

    # If no match found, return None
    return None

# Scrape playoff odds from moneypuck.com
async def get_playoff_odds(team_name=None):
    """Fetch playoff odds using Selenium and filter for a specific team if provided."""
    url = "https://moneypuck.com/predictions.htm"

    # Setup Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without opening a browser
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        await asyncio.sleep(5)  # Wait for JavaScript to load

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        div_content = soup.find('div', {'id': 'includedContent'})

        if not div_content or not div_content.text.strip():
            print("Error: No content found in the div.")
            return "Error: No data found."

        # Extract all team abbreviations and their corresponding playoff odds
        teams_odds = {}

        rows = div_content.find_all('tr')
        for row in rows:
            b_tag = row.find('b')  # Find the <b> tag for the team abbreviation
            td_tags = row.find_all('td')  # Find all <td> tags in the row

            if b_tag and len(td_tags) > 1:
                team_abbr = b_tag.get_text().strip()
                playoff_odds = td_tags[1].get_text().strip()  # The second <td> contains the playoff odds
                teams_odds[team_abbr] = playoff_odds

        print("Teams and Playoff Odds:", teams_odds)  # Print the teams and their playoff odds

        # If a team input is provided, check if it's a full name or abbreviation
        if team_name:
            # Check if the input is an abbreviation (i.e., 3 letters)
            team_abbr = team_name.strip().upper()
            
            if len(team_abbr) == 3:  # It's likely an abbreviation
                playoff_odds = teams_odds.get(team_abbr)
                if playoff_odds:
                    return f"Playoff odds for {team_abbr}: {playoff_odds}"
                else:
                    return f"Playoff odds for abbreviation '{team_abbr}' not found."
            
            else:  # It's a full team name, convert it to abbreviation
                team_abbr = convert_team_name_to_abbreviation(team_name.strip())
                if not team_abbr:
                    return f"Error: Team name '{team_name}' not recognized."

                # Look up the playoff odds for the abbreviation
                playoff_odds = teams_odds.get(team_abbr.upper())  # Ensure abbreviation is uppercase
                if playoff_odds:
                    return f"Playoff odds for {team_name} ({team_abbr}): {playoff_odds}"
                else:
                    return f"Playoff odds for abbreviation '{team_abbr}' not found."

        else:
            return teams_odds  # Return the full dictionary of teams and playoff odds

    except Exception as e:
        return f"Error: {e}"

    finally:
        driver.quit()


#NHL API

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



async def fetch_player_stats(player_id):
    """Fetch player statistics from the NHL API."""
    NHL_PLAYER_STATS_URL = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={player_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(NHL_PLAYER_STATS_URL) as response:
            if response.status != 200:
                return None, "Error: Unable to fetch player stats."
            
            data = await response.json()
            return data.get("data", []), None

async def get_player_points(player_input):
    """Fetch a player's total points (goals + assists) from the NHL API."""

    NHL_YEAR = get_current_season()  # Fetch the current season dynamical
    
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
                print(data)

                # Check if stats exist
                if not data['data']:
                    return f"🏒 {player_name} has not recorded any stats this season."

                # Filter stats for the current season
                current_season = "NHL_YEAR"  # Update this for the current season
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

async def process_player_stats(player_id, player_name):
    """Retrieve and process a player's statistics for the current season."""
    stats_data, error = await fetch_player_stats(player_id)
    if error:
        return error

    if not stats_data:
        return f"🏒 {player_name} has not recorded any stats this season."

    current_season = await get_current_season()
    current_season_stats = next((stats for stats in stats_data if str(stats["seasonId"]) == current_season), None)

    if not current_season_stats:
        return f"🏒 {player_name} has not recorded any stats this season."

    goals = current_season_stats.get("goals", 0)
    assists = current_season_stats.get("assists", 0)
    points = goals + assists

    return f"🏒 {player_name} has {points} points ({goals} goals + {assists} assists) this season!"

async def get_player_points_new(player_input):
    """Fetch a player's total points (goals + assists) from the NHL API."""
    
    if player_input.isdigit():  # Player ID input
        player_id = int(player_input)
        player_name = await get_player_info(player_id)
        if not player_name:
            return f"Error: Player ID {player_id} not found."

        return await process_player_stats(player_id, player_name)

    # If input is a last name, search for matching players
    players = await search_players_by_last_name(player_input)
    if isinstance(players, str):  # Error message case
        return players

    if len(players) > 1:  # Multiple matches, prompt for ID
        return "Multiple players found. Please specify by ID:\n" + "\n".join(
            [f"- {full_name} (ID: {player_id})" for player_id, full_name in players]
        )

    player_id, player_name = players[0]
    return await process_player_stats(player_id, player_name)

#Team functions 

async def get_standings(query): 
    """Fetch the current season standings for a given NHL team, division, conference, all teams, or playoff picture."""

    NHL_TEAM_STANDINGS_URL = "https://api-web.nhle.com/v1/standings/now"

    async with aiohttp.ClientSession() as session:
        async with session.get(NHL_TEAM_STANDINGS_URL) as response:
            if response.status != 200:
                return "Error: Unable to fetch team standings."

            data = await response.json()
            standings = data.get("standings", [])

            if not isinstance(standings, list):  # Ensure standings is a list
                return "Error: Unexpected data format from NHL API."

            # Define NHL divisions and conferences
            divisions = ["Pacific", "Central", "Atlantic", "Metropolitan"]
            conference_aliases = {
                "west": "Western",
                "western": "Western",
                "east": "Eastern",
                "eastern": "Eastern"
            }

            query_lower = query.lower()

            # Return all NHL teams sorted by points
            if query_lower == "all":
                all_teams = sorted(standings, key=lambda x: x.get("points", 0), reverse=True)
                standings_text = "🏆 **NHL League Standings:**\n"
                for rank, team in enumerate(all_teams, start=1):
                    team_name = team.get("teamName", {}).get("default", "Unknown Team")
                    team_points = team.get("points", 0)
                    standings_text += f"{rank}. {team_name} - {team_points} pts\n"
                return standings_text

            # Playoff standings
            if query_lower in ["playoffs west", "playoffs east"]:
                conference_name = "Western" if "west" in query_lower else "Eastern"
                conference_teams = [team for team in standings if team.get("conferenceName", "") == conference_name]
                
                # Sort teams by points
                conference_teams.sort(key=lambda x: x.get("points", 0), reverse=True)

                # Separate by divisions
                div1, div2 = ("Pacific", "Central") if "west" in query_lower else ("Metropolitan", "Atlantic")
                div1_teams = [team for team in conference_teams if team.get("divisionName", "") == div1][:3]
                div2_teams = [team for team in conference_teams if team.get("divisionName", "") == div2][:3]

                # Get wild card teams (next 2 best teams outside of top 3 in each division)
                remaining_teams = [team for team in conference_teams if team not in div1_teams + div2_teams]
                wild_card_teams = remaining_teams[:2]

                # Get next 2 teams outside playoffs
                outside_teams = remaining_teams[2:4]

                # Format output
                standings_text = f"🏆 **{conference_name} Conference Playoff Picture** 🏆\n\n"
                standings_text += f"**{div1} Division:**\n"
                for i, team in enumerate(div1_teams, 1):
                    standings_text += f"{i}. {team['teamName']['default']} - {team['points']} pts\n"

                standings_text += f"\n**{div2} Division:**\n"
                for i, team in enumerate(div2_teams, 1):
                    standings_text += f"{i}. {team['teamName']['default']} - {team['points']} pts\n"

                standings_text += f"\n**Wild Card Teams:**\n"
                for i, team in enumerate(wild_card_teams, 1):
                    standings_text += f"WC{i}. {team['teamName']['default']} - {team['points']} pts\n"

                standings_text += f"\n**Chasing the Playoffs:**\n"
                for i, team in enumerate(outside_teams, 1):
                    standings_text += f"{i}. {team['teamName']['default']} - {team['points']} pts\n"

                return standings_text

            # Check if input is a division
            if query_lower in [d.lower() for d in divisions]:
                division_teams = [team for team in standings if team.get("divisionName", "").lower() == query_lower]
                if not division_teams:
                    return f"Error: No teams found in the {query.title()} Division."
                division_teams.sort(key=lambda x: x.get("points", 0), reverse=True)
                standings_text = f"📊 {query.title()} Division Standings:\n"
                for rank, team in enumerate(division_teams, start=1):
                    standings_text += f"{rank}. {team['teamName']['default']} - {team['points']} pts\n"
                return standings_text

             # Check if input is a conference (supports "West/Western" and "East/Eastern")
            if query_lower in conference_aliases:
                conference_name = conference_aliases[query_lower]
                conference_teams = [team for team in standings if team.get("conferenceName", "") == conference_name]
                if not conference_teams:
                    return f"Error: No teams found in the {conference_name} Conference."
                conference_teams.sort(key=lambda x: x.get("points", 0), reverse=True)
                standings_text = f"🌎 {conference_name} Conference Standings:\n"
                for rank, team in enumerate(conference_teams, start=1):
                    standings_text += f"{rank}. {team['teamName']['default']} - {team['points']} pts\n"
                return standings_text

            # If not a division or conference, assume it's a team query
            for team in standings:
                team_name_english = team.get("teamName", {}).get("default", "Unknown Team")
                team_name_french = team.get("teamName", {}).get("fr", "Unknown Team")
                team_abbrev = team.get("teamAbbrev", {}).get("default", "Unknown Team")

                if (query_lower in team_name_english.lower() or
                    query_lower in team_name_french.lower() or
                    query_lower == team_abbrev.lower()):
                    team_points = team.get("points", 0)
                    return f"🏒 {team_name_english} currently has {team_points} points this season!"

            return f"Error: Team, division, conference, or 'playoffs' keyword '{query}' not found. Please check your spelling."

#Tracking Functions 

async def track_player_events(player_id, channel, player_name):
    """Track a player's goals and goals against in real-time."""
    last_goals = None
    last_goals_against = None

    NHL_YEAR = get_current_season()  # Fetch the current season dynamical

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
        await message.channel.send("I am alive and listening!" + " Version: " + VERSION)

    if content_lower.startswith("!standings"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("**🏒 Available `!standings` Commands:**\n"
                    "`!standings all` - Shows full NHL standings\n"
                    "`!standings <team name>` - Shows a specific team's points (e.g., `!standings bruins`)\n"
                    "`!standings <division>` - Shows a division's standings (e.g., `!standings pacific`)\n"
                    "`!standings <conference>` - Shows a conference's standings (e.g., `!standings western`)\n"
                    "`!standings Playoffs west` - Shows the Western Conference playoff picture\n"
                    "`!standings Playoffs east` - Shows the Eastern Conference playoff picture\n")
            return

        team_name = parts[1]
        result = await get_standings(team_name)
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

    if content_lower.startswith("!playoffodds"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return

        # Extract the team name from the command (if any)
        command_parts = content_lower.split(" ")
        team_name = " ".join(command_parts[1:]).strip()  # Get the team name after the command

        # If no team name is provided, instruct the user to provide one
        if not team_name:
            await message.channel.send("Please provide a team name after the command, e.g., `!playoffodds Team A`.")
        else:
            # Convert the team name to its abbreviation
            team_abbreviation = convert_team_name_to_abbreviation(team_name)
        
            # Check if the team abbreviation was successfully found
            if team_abbreviation:
                # Print the abbreviated name to the console for debugging purposes
                print(f"Converted Team Name: {team_abbreviation}")
            
                # Fetch the playoff odds for the team using the abbreviation
                odds = await get_playoff_odds(team_abbreviation)
                await message.channel.send(odds)
            else:
                # If the team name couldn't be converted, send an error message
                await message.channel.send(f"Sorry, I couldn't find the team '{team_name}'. Please make sure the name is correct and try again.")

        
    # Shitpost messages
    if content_lower.startswith("!freepetey"):
        await message.channel.send("We will hold Petey hostage until our demands are met!")
        # Add Channel Command

    # Admin Override Commands (Add & Delete Channel)
    if ADMIN_OVERRIDE:
        if content_lower.startswith("!addchannel"):
            allowed_channels = [DISCORD_INFO_CHANNEL_ID]  # Restrict command usage to specific channels
            if message.channel.id not in allowed_channels:
                return

            parts = message.content.split(maxsplit=1)
            if len(parts) != 2:
                await message.channel.send("Usage: `!addchannel <channel_name>`")
                return

            channel_name = parts[1]
            guild = message.guild

            # Check if the channel already exists
            existing_channel = discord.utils.get(guild.channels, name=channel_name)
            if existing_channel:
                await message.channel.send(f"A channel named '{channel_name}' already exists.")
                return

            # Create the channel
            new_channel = await guild.create_text_channel(channel_name)
            await message.channel.send(f"✅ Channel '{new_channel.name}' has been created!")

        if content_lower.startswith("!deletechannel"):
            allowed_channels = [DISCORD_INFO_CHANNEL_ID]  # Restrict command usage to specific channels
            if message.channel.id not in allowed_channels:
                return

            parts = message.content.split(maxsplit=1)
            if len(parts) != 2:
                await message.channel.send("Usage: `!deletechannel <channel_name>`")
                return

            channel_name = parts[1]
            guild = message.guild

            # Find the channel
            channel_to_delete = discord.utils.get(guild.channels, name=channel_name)
            if not channel_to_delete:
                await message.channel.send(f"❌ No channel named '{channel_name}' found.")
                return

            # Delete the channel
            await channel_to_delete.delete()
            await message.channel.send(f"🗑️ Channel '{channel_name}' has been deleted.")

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
