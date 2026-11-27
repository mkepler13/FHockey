import discord
from discord.ext import commands
import aiohttp # Import aiohttp for asynchronous HTTP requests
import asyncio  # Import asyncio for handling asynchronous operations
import os # Import os for interacting with the operating system
import tempfile
from collections import defaultdict
import logging  # Import logging for logging messages to console
from dotenv import load_dotenv # Import load_dotenv from dotenv for loading environment variables
from bs4 import BeautifulSoup  # Import BeautifulSoup for scraping
import requests  # Import requests for HTTP requests
from selenium import webdriver # Import webdriver for browser automation
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime # Import datetime for date/time manipulation
#import difflib  # Import difflib for string matching
import urllib.parse # Import urllib for URL parsing
import io # Import io for handling file-like 
import random
#from fastapi import FastAPI
from typing import Optional
import re
import pytesseract
import pypdfium2 as pdfium
from PIL import Image
import json
import xml.etree.ElementTree as ET
import unicodedata

VERSION = "0.5.0"

# Load environment variables from .env file
load_dotenv()

# Get the tokens from the .env file
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_BOTSPAM_CHANNEL_ID = int(os.getenv("DISCORD_BOTSPAM_CHANNEL_ID", "0"))
DISCORD_TRADE_CHANNEL_ID = int(os.getenv("DISCORD_TRADE_CHANNEL_ID", "0"))
DISCORD_INFO_CHANNEL_ID = int(os.getenv("DISCORD_INFO_CHANNEL_ID", "0"))
CSRF_TOKEN = "YOUR_CSRF_TOKEN"

# Check if the token is found
if TOKEN is None:
    raise ValueError("No DISCORD_BOT_TOKEN found in .env file.")
if DISCORD_BOTSPAM_CHANNEL_ID is None:
    raise ValueError("No DISCORD_BOTSPAM_CHANNEL_ID found in .env file.")
if DISCORD_TRADE_CHANNEL_ID is None:
    raise ValueError("No DISCORD_TRADE_CHANNEL_ID found in .env file.")
if DISCORD_INFO_CHANNEL_ID is None:
    raise ValueError("No DISCORD_INFO_CHANNEL_ID found in .env file.")

# === Fantrax API health check (runs once at startup) ===
FANTRAX_API = "http://localhost:8000"
FANTRAX_ENABLED = False

print("Checking Fantrax API status...")

try:
    resp = requests.get(f"{FANTRAX_API}/status", timeout=5)
    if resp.status_code == 200 and resp.json().get("login_success", False):
        FANTRAX_ENABLED = True
        print("Fantrax service is online and logged in.")
    else:
        print("Fantrax API reachable but not logged in.")
except Exception as e:
    print(f"Could not contact Fantrax API: {e}")

print(f"FANTRAX_ENABLED = {FANTRAX_ENABLED}")

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True  # Allow reading messages
intents.guilds = True
intents.message_content = True  # Required to read message content

client = discord.Client(intents=intents)

intents = discord.Intents.default()  # Or use discord.Intents.all() if needed
bot = commands.Bot(command_prefix="!", intents=intents)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
print("Tesseract exe:", pytesseract.pytesseract.tesseract_cmd)
print("TESSDATA_PREFIX:", os.environ.get("TESSDATA_PREFIX"))
print("Tesseract version:", pytesseract.get_tesseract_version())
print("Available langs:", pytesseract.get_languages(config=""))

# NHL API Endpoints
NHL_STATS_URL = "https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={}"
NHL_PLAYER_INFO_URL = "https://api-web.nhle.com/v1/player/{}/landing"
NHL_Hits = "https://api.nhle.com/stats/rest/en/skater/realtime?limit=-1&cayenneExp=seasonId={}%20and%20gameTypeId=2%20and%20playerId={}"

# Other API Endpoints
IASIP_API_URL = "https://iasip.app/api/title/"
DEFAULT_CSRF_URL = "https://iasip.app"

ADMIN_OVERRIDE = False  # Set this to True to allow add/delete channel commands

# Tracked player

plus_minus_tracker = [
    {"name": "Tyler Myers", "id": 8474574}
]

shot_on_net_tracker = [
    {"name": "Cody Ceci", "id": 8476879}
]

REDDIT_HEADERS = {
    "User-Agent": "FantasyHockeyBot/1.0 by u/Falsey8"
}


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
    {"name": "Zach Werenski", "id": 8478460},
    {"name": "Mark Stone", "id": 8475913},
    {"name": "Eeli Tolvanen", "id": 8480009},
    {"name": "Connor Garland", "id": 8478856},
    {"name": "Alex Tuch", "id": 8477949},
    {"name": "Cole Caufield", "id": 8481540},
    {"name": "Jack Hughes", "id": 8481559},
    {"name": "Tage Thompson", "id": 8479420},
    {"name": "Juraj Slafkovsky", "id": 8483515},
    {"name": "Dylan Larkin", "id": 8477946},
    {"name": "Willius Nylander", "id": 8477939},
    {"name": "Maitch Marner", "id": 8478483},
    {"name": "Tom Wilson", "id": 8476880},
    {"name": "Mikael Granlund", "id": 8475798},
    {"name": "Nathan MacKinnon", "id": 8477492},
    {"name": "Leon Draisaitl", "id": 8477934},
    {"name": "Brad Marchand", "id": 8473419},
    {"name": "Brock Boeser", "id": 8478444},
    {"name": "Jacob Trouba", "id": 8476885},
    {"name": "Aleksander Barkov", "id": 8477493},
    {"name": "Sidney Crosby", "id": 8471675},
    {"name": "Steven Stamkos", "id": 8474564},
    {"name": "Alex DeBrincat", "id": 8479337},
    {"name": "Shane Wright", "id": 8483524},
    {"name": "Matty Beniers", "id": 8482665},
    {"name": "Adam \"@Foxyclean\" Fox", "id": 8479323}
]

#team name dictionary
TEAM_NAME_TO_ABBREVIATION = {
    "Anaheim Ducks": "ANA", "Ducks d'Anaheim": "ANA", "Ducks": "ANA", "Anaheim": "ANA",
    "Boston Bruins": "BOS", "Bruins de Boston": "BOS", "Bruins": "BOS", "Boston": "BOS",
    "Buffalo Sabres": "BUF", "Sabres de Buffalo": "BUF","Sabres": "BUF", "Buffalo": "BUF",
    "Calgary Flames": "CGY", "Flames de Calgary": "CGY", "Calgary": "CGY", "Flames": "CGY",
    "Carolina Hurricanes": "CAR", "Hurricanes de la Caroline": "CAR", "Carolina": "CAR", "Hurricanes": "CAR", "Canes": "CAR",
    "Chicago Blackhawks": "CHI", "Blackhawks de Chicago": "CHI", "Blackhawks": "CHI", "Chicago": "CHI", "Hawks": "CHI",
    "Colorado Avalanche": "COL", "Avalanche du Colorado": "COL", "Colorado": "COL", "Avalanche": "COL", "Avs": "COL",
    "Columbus Blue Jackets": "CBJ", "Blue Jackets de Columbus": "CBJ", "Columbus": "CBJ", "Blue Jackets": "CBJ", "Jackets": "CBJ",
    "Dallas Stars": "DAL", "Stars de Dallas": "DAL", "Dallas": "DAL", "Stars": "DAL",
    "Detroit Red Wings": "DET", "Red Wings de Détroit": "DET", "Detroit": "DET", "Red Wings": "DET", "Wings": "DET",
    "Edmonton Oilers": "EDM", "Oilers d'Edmonton": "EDM", "Edmonton": "EDM", "Oilers": "EDM",
    "Florida Panthers": "FLA", "Panthers de la Floride": "FLA", "Florida": "FLA", "Panthers": "FLA", "Cats": "FLA",
    "Los Angeles Kings": "LAK", "Kings de Los Angeles": "LAK", "Los Angeles": "LAK", "Kings": "LAK",
    "Minnesota Wild": "MIN", "Wild du Minnesota": "MIN", "Minnesota": "MIN", "Wild": "MIN",
    "Montreal Canadiens": "MTL", "Canadiens de Montréal": "MTL", "Montreal": "MTL", "Canadiens": "MTL", "Habs": "MTL",
    "Nashville Predators": "NSH", "Predators de Nashville": "NSH", "Nashville": "NSH", "Predators": "NSH", "Preds": "NSH",
    "New Jersey Devils": "NJD", "Devils du New Jersey": "NJD", "New Jersey": "NJD", "Devils": "NJD",
    "New York Islanders": "NYI", "Islanders de New York": "NYI","Islanders": "NYI", "Isls": "NYI",
    "New York Rangers": "NYR", "Rangers de New York": "NYR", "Rangers": "NYR", "Rags": "NYR",
    "Ottawa Senators": "OTT", "Senateurs d'Ottawa": "OTT", "Ottawa": "OTT", "Senators": "OTT", "Sens": "OTT",
    "Philadelphia Flyers": "PHI", "Flyers de Philadelphie": "PHI", "Philadelphia": "PHI", "Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "Penguins de Pittsburgh": "PIT",  "Pittsburgh": "PIT", "Penguins": "PIT",
    "San Jose Sharks": "SJS", "Sharks de San Jose": "SJS", "San Jose": "SJS", "Sharks": "SJS",
    "Seattle Kraken": "SEA", "Kraken de Seattle": "SEA", "Seattle": "SEA", "Seattle": "SEA",
    "St. Louis Blues": "STL", "Blues de Saint-Louis": "STL", "St. Louis": "STL", "Blues": "STL",
    "Tampa Bay Lightning": "TBL", "Lightning de Tampa Bay": "TBL", "Tampa Bay": "TBL", "Lightning": "TBL", "Bolts": "TBL",
    "Toronto Maple Leafs": "TOR", "Maple Leafs de Toronto": "TOR", "Toronto": "TOR", "Maple Leafs": "TOR", "Leafs": "TOR",
    "Utah Mammoth": "UTA", "Mammoth de l'Utah": "UTA", "Utah": "UTA", "Mammoth": "UTA",
    "Vancouver Canucks": "VAN", "Canucks de Vancouver": "VAN", "Vancouver": "VAN", "Canucks": "VAN", "Nucks": "VAN",
    "Vegas Golden Knights": "VGK", "Golden Knights de Vegas": "VGK", "Vegas": "VGK", "Golden Knights": "VGK", "Knights": "VGK",
    "Washington Capitals": "WSH", "Capitals de Washington": "WSH", "Washington": "WSH", "Capitals": "WSH", "Caps": "WSH",
    "Winnipeg Jets": "WPG", "Jets de Winnipeg": "WPG", "Jets": "WPG", "Winnipeg": "WPG",
}


#check if fantrax script is working
def check_fantrax_status():
    try:
        resp = requests.get(f"{FANTRAX_API}/status").json()
        return resp.get("login_success", False)
    except Exception as e:
        print("Error contacting Fantrax service:", e)
        return False

# API YEAR
def get_current_season():
    """Dynamically determine the current NHL season."""
    now = datetime.now()
    year = now.year
    if now.month < 7:  # NHL season starts in October and ends around June
        return f"{year - 1}{year}"
    return f"{year}{year + 1}"


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


# Scrape world juniors

HYDRA_BASE = "https://stats.iihf.com/Hydra/37/"
HYDRA_INDEX = HYDRA_BASE + "index.html"

# --- Configure these to your local Tesseract install ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Finds "Player Statistics by Team" PDFs like: IHM0370CAN_83_2_0.pdf
TEAM_PDF_RE = re.compile(r'(IHM0370([A-Z]{3})_83_(\d+)_0\.pdf)', re.I)

ROW_RE = re.compile(
    r"""^\s*
    (?P<rank>\d+)\.?\s+
    (?P<name>.+?)\s+
    (?P<jersey>\d{1,2})\s+
    (?P<team>[A-Z]{3})\s+
    (?P<pos>[A-Z])\s+
    (?P<gp>\d+)\s+
    (?P<g>\d+)\s+
    (?P<a>\d+)\s+
    (?P<pts>\d+)\s+
    (?P<pim>\d+)
    (?:\s+(?P<pm>[+-]?\d+))?
    \s*$
    """,
    re.VERBOSE
)

def _safe_int(s, default=0):
    try:
        return int(str(s).strip())
    except:
        return default

def _normalize_header_tokens(line: str):
    # Normalize OCR weirdness: punctuation and repeated spaces
    line = line.replace("No.", "No").replace("Pos.", "Pos")
    line = re.sub(r"\s+", " ", line).strip()
    # split into tokens, strip dots/colons
    toks = [re.sub(r"[^\w+/-]", "", t) for t in line.split()]
    toks = [t for t in toks if t]
    return [t.upper() for t in toks]

def _looks_like_header(toks):
    # Must include core stat columns
    needed = {"GP", "G", "A", "PTS", "PIM"}
    return needed.issubset(set(toks)) and ("NAME" in toks or "NO" in toks)

POS_SET = {"F", "D", "G"}

def _clean_and_split_tokens(line: str):
    # Normalize OCR junk
    line = line.replace("°", " ").replace("º", " ").replace("·", " ")
    line = re.sub(r"\s+", " ", line).strip()

    # Split tokens, but also fix common OCR merge "3.1" -> "3 1" (only digit-dot-digit)
    fixed = []
    for t in line.split():
        t2 = re.sub(r"^(\d)\.(\d)$", r"\1 \2", t)  # only 1-digit . 1-digit
        fixed.extend(t2.split())

    return fixed

def _parse_player_table_from_ocr(text: str, team_hint: str, debug=False):
    players = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    header_tokens = None
    for ln in lines:
        toks = _normalize_header_tokens(ln)
        if _looks_like_header(toks):
            header_tokens = toks
            if debug:
                print("DEBUG: Found header:", header_tokens)
            break

    if not header_tokens:
        return players  # no table on this page

    for raw in lines:
        toks = _clean_and_split_tokens(raw)
        if len(toks) < 6:
            continue

        # jersey number must be first token
        if not toks[0].isdigit():
            continue
        jersey = int(toks[0])

        # remove captain markers that OCR sometimes adds in the middle
        toks = [t for t in toks if t not in {"+A", "+C"}]

        # find POS token location
        pos_idx = None
        for i in range(1, min(len(toks), 20)):  # early tokens only (name+pos are early)
            if toks[i] in POS_SET:
                pos_idx = i
                break
        if pos_idx is None:
            continue

        pos = toks[pos_idx]

        # name is everything between jersey and pos
        name_tokens = toks[1:pos_idx]
        name = " ".join(name_tokens).strip()
        if not name or len(name) < 2:
            continue

        # After POS, collect integers in order: GP, G, A, PTS, PIM
        nums = []
        for t in toks[pos_idx + 1:]:
            # +/- can be like +4 or -1, ignore it for the “5 required ints”
            if re.fullmatch(r"[+-]\d+", t):
                continue
            if t.isdigit():
                nums.append(int(t))
                if len(nums) >= 5:
                    break

        if len(nums) < 5:
            # not enough stats found on this line
            continue

        gp, g, a, pts, pim = nums[:5]

        players.append({
            "player": name,
            "team": team_hint,
            "pos": pos,
            "gp": gp,
            "goals": g,
            "assists": a,
            "points": pts if pts != 0 else (g + a),
            "pim": pim,
        })

    if debug:
        print(f"DEBUG: {team_hint} parsed rows: {len(players)}")
        if players[:3]:
            print("DEBUG sample:", players[:3])

    return players

def _ocr_pdf_bytes(pdf_bytes: bytes, scale: float = 3.5, debug=False):
    """
    Returns OCR text per page.
    """
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        doc = pdfium.PdfDocument(pdf_path)
        page_texts = []
        for i in range(len(doc)):
            page = doc[i]
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
            text = pytesseract.image_to_string(img, lang="eng")
            page_texts.append(text)

        return page_texts
    finally:
        try:
            os.remove(pdf_path)
        except:
            pass

async def _fetch_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} for {url}")
            return await resp.read()

async def _get_latest_team_stat_pdfs(debug=False) -> dict:
    """
    Returns dict: { 'CAN': 'https://.../IHM0370CAN_83_2_0.pdf', ... }
    Picks highest revision number per team.
    """
    html = (await _fetch_bytes(HYDRA_INDEX)).decode("utf-8", errors="ignore")

    best = {}  # team -> (rev, filename)
    for filename, team, rev in TEAM_PDF_RE.findall(html):
        rev = int(rev)
        team = team.upper()
        if team not in best or rev > best[team][0]:
            best[team] = (rev, filename)

    out = {team: HYDRA_BASE + fn for team, (rev, fn) in best.items()}
    if debug:
        print("DEBUG: Found team PDFs:", out)
    return out

async def get_u20_world_juniors_stats(limit=None, debug=False):
    """
    Returns merged list of ALL players across teams, sorted by points then goals.
    """
    team_pdfs = await _get_latest_team_stat_pdfs(debug=debug)

    all_players = []
    for team, pdf_url in sorted(team_pdfs.items()):
        if debug:
            print(f"\nDEBUG: Team {team} -> {pdf_url}")

        pdf_bytes = await _fetch_bytes(pdf_url)

        # OCR each page
        page_texts = _ocr_pdf_bytes(pdf_bytes, scale=3.5, debug=debug)

        team_players = []
        for page_i, text in enumerate(page_texts, start=1):
            if debug:
                print(f"DEBUG: {team} page {page_i} OCR preview:\n{text[:300]}\n")

            team_players.extend(_parse_player_table_from_ocr(text, team_hint=team, debug=debug))

        if debug:
            print(f"DEBUG: Parsed {len(team_players)} players for {team}")

        all_players.extend(team_players)

    # De-dupe (sometimes goalies/extra lines can duplicate); key by (team,name)
    dedup = {}
    for p in all_players:
        key = (p["team"], p["player"])
        # keep the one with higher GP/PTS if duplicates occur
        if key not in dedup:
            dedup[key] = p
        else:
            if (p["gp"], p["points"]) > (dedup[key]["gp"], dedup[key]["points"]):
                dedup[key] = p

    merged = list(dedup.values())
    merged.sort(key=lambda p: (p["points"], p["goals"]), reverse=True)

    if limit:
        merged = merged[:limit]

    if debug:
        print("\nDEBUG: Total merged players:", len(merged))
        print("DEBUG: First 5:", merged[:5])

    return merged

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

# Image downloading 
async def send_embedded_image(channel, image_url):
    """
    Downloads an image from a given URL and sends it as an embedded image in Discord.
    Supports direct image URLs and Reddit media redirect URLs.
    """
    # Extract actual image URL if it's a Reddit media redirect
    parsed_url = urllib.parse.urlparse(image_url)
    if parsed_url.netloc == "www.reddit.com" and "url=" in parsed_url.query:
        query_params = urllib.parse.parse_qs(parsed_url.query)
        image_url = query_params.get("url", [None])[0]  # Extract the real URL
    
    if not image_url:
        return await channel.send("Invalid image URL.")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    return await channel.send("Failed to download image. URL might be broken.")

                content_type = resp.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    return await channel.send("The URL does not point to a valid image.")

                data = io.BytesIO(await resp.read())  # Read image into memory
                filename = "image." + content_type.split("/")[-1]  # Determine file extension
                file = discord.File(data, filename=filename)

                await channel.send(file=file)  # Send only the file (no embed)
        except aiohttp.ClientError:
            await channel.send("Unable to retrieve the image. The URL might be incorrect.")

#Always Sunny Posting

# Function to get CSRF token (manual extraction)
async def get_csrf_token(session):
    async with session.get(DEFAULT_CSRF_URL) as response:
        cookies = response.cookies
        csrf_token = cookies.get('CSRF-TOKEN')  # Adjust the cookie name if needed
        if csrf_token:
            return csrf_token.value  # Return the string value of the CSRF token
        return None  # If no CSRF token found

async def save_title(quote, CSRF_TOKEN):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": CSRF_TOKEN,  # Use the CSRF token passed as an argument
        "X-Requested-With": "XMLHttpRequest"
    }
    
    async with aiohttp.ClientSession() as session:
        data = {"text": quote}
        
        # Send POST request to save the title
        async with session.post(IASIP_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                key = response_data.get("key")
                return f"https://iasip.app/{key}"
            else:
                return "Failed to save title"
            

async def get_latest_fantasy_hockey_image(username: str) -> Optional[str]:
    url = f"https://www.reddit.com/user/{username}/submitted.json?limit=15"

    async with aiohttp.ClientSession(headers=REDDIT_HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    posts = data.get("data", {}).get("children", [])

    for post in posts:
        p = post.get("data", {})
        title = p.get("title", "")

        if not title.startswith("Fantasy Hockey Schedule Summary"):
            continue

        # Regular image post
        if p.get("post_hint") == "image":
            return p.get("url")

        # Gallery post (first image)
        if p.get("is_gallery"):
            media = p.get("media_metadata", {})
            for item in media.values():
                if "s" in item and "u" in item["s"]:
                    return item["s"]["u"].replace("&amp;", "&")

    return None

#Twitter Posting


# ==========================================
# LIVE HOCKEY INSIDER RSS FEED
# ==========================================

RSS_FEEDS = {
    "FriedgeHNIC": (
        "https://rsshub.app/twitter/user/FriedgeHNIC"
    ),
    "PierreVLeBrun": (
        "https://rsshub.app/twitter/user/PierreVLeBrun"
    )
}

RSS_STATE_FILE = "tweet_state.json"

# This task is started once when the Discord bot connects.
rss_monitor_task = None


def load_rss_state():
    """Load the last processed entry ID for each account."""
    try:
        with open(RSS_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_rss_state(state):
    """Save processed entry IDs to prevent duplicate posts."""
    with open(RSS_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def get_xml_child(element, name):
    """Find a direct XML child by its local tag name."""
    for child in element:
        if child.tag.split("}")[-1] == name:
            return child
    return None


def parse_rss_entries(xml_text):
    """Parse RSS or Atom entries into a common format."""
    root = ET.fromstring(xml_text)

    entries = []

    for item in root.iter():
        tag = item.tag.split("}")[-1]

        if tag not in ("item", "entry"):
            continue

        entry_id = None
        link = None
        title = ""
        description = ""

        for child in item:
            child_name = child.tag.split("}")[-1]

            if child_name in ("guid", "id"):
                entry_id = (child.text or "").strip()

            elif child_name == "link":
                link = (
                    child.attrib.get("href")
                    or (child.text or "").strip()
                )

            elif child_name == "title":
                title = child.text or ""

            elif child_name in ("description", "summary", "encoded", "content"):
                description = child.text or description

        entry_id = entry_id or link

        if not entry_id:
            continue

        # Convert any HTML in the tweet into readable text.
        text_content = BeautifulSoup(
            description or title,
            "html.parser"
        ).get_text(" ", strip=True)

        entries.append({
            "id": entry_id,
            "link": link,
            "text": text_content or title
        })

    return entries


async def fetch_rss_feed(session, url):
    """Download and parse one RSS feed."""
    async with session.get(url) as response:
        if response.status != 200:
            raise RuntimeError(
                f"RSS returned HTTP {response.status}"
            )

        xml_text = await response.text()

    return parse_rss_entries(xml_text)


async def post_rss_entry(channel, username, entry):
    """Post a new insider update into botspam."""

    embed = discord.Embed(
        title=f"🏒 @{username}",
        description=entry["text"][:4000],
        color=discord.Color.blue()
    )

    if entry.get("link"):
        embed.url = entry["link"]

    await channel.send(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )


async def monitor_rss_feeds():
    """Continuously monitor the selected hockey insider feeds."""

    channel = client.get_channel(DISCORD_BOTSPAM_CHANNEL_ID)

    if channel is None:
        try:
            channel = await client.fetch_channel(
                DISCORD_BOTSPAM_CHANNEL_ID
            )
        except Exception as e:
            logging.error(f"Could not find botspam channel: {e}")
            return

    state = load_rss_state()

    timeout = aiohttp.ClientTimeout(total=25)

    headers = {
        "User-Agent": "FantasyHockeyDiscordBot/1.0"
    }

    logging.info("Starting hockey insider RSS monitoring.")

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        while True:

            for username, feed_url in RSS_FEEDS.items():

                try:
                    entries = await fetch_rss_feed(
                        session,
                        feed_url
                    )

                    if not entries:
                        logging.info(
                            f"No RSS entries found for @{username}"
                        )
                        continue

                    # Feeds normally return newest entries first.
                    newest_id = entries[0]["id"]

                    # First run: save the latest entry without
                    # posting historical updates.
                    if username not in state:
                        state[username] = newest_id
                        save_rss_state(state)

                        logging.info(
                            f"Initialized @{username} RSS tracking."
                        )
                        continue

                    last_id = state[username]

                    # Find the previously processed entry.
                    old_index = next(
                        (
                            i for i, entry in enumerate(entries)
                            if entry["id"] == last_id
                        ),
                        None
                    )

                    if old_index is None:
                        # Previous entry has fallen out of the feed.
                        # Post only the newest one to avoid flooding.
                        new_entries = entries[:1]
                    else:
                        # Process new entries oldest first.
                        new_entries = entries[:old_index][::-1]

                    for entry in new_entries:

                        await post_rss_entry(
                            channel,
                            username,
                            entry
                        )

                        # Save only after successful Discord posting.
                        state[username] = entry["id"]
                        save_rss_state(state)

                        logging.info(
                            f"Posted new update from @{username}"
                        )

                except Exception as e:
                    logging.error(
                        f"RSS error for @{username}: {e}"
                    )

            # Random interval between checks.
            await asyncio.sleep(random.randint(50, 60))


#Reading Functions 

@client.event
async def on_message(message):
    if message.author == client.user: #ignore if message is from bot
        return
    content_lower = message.content.lower() # Convert the message content to lowercase for case-insensitive comparison

    if content_lower.startswith("!test"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID, DISCORD_TRADE_CHANNEL_ID]  # Check if the message is in one of the allowed channels
        if message.channel.id not in allowed_channels:
            return
        await message.channel.send("I am alive and listening!" + " Version: " + VERSION)

    elif content_lower.startswith("!help"):
        await message.channel.send("**🏒 Available Commands:**\n"
                    "`!test` - Check Bot status and Version\n"
                    "`!playerpoints <player name or ID>` - Shows a Players Points\n"
                    "`!standings` - Shows NHL Current Standings\n"
                    "`!playoffodds <Team>` - Shows a team's current Playoff odds\n"
                    "`!weekly` - Shows this weeks daily game schedule\n"
                    "`---- Fantrax Commands ----`\n"
                    "`!fantraxstandings` - Shows the current Fantrax Standings\n"
                    "`!fantraxteams` - Shows the Fantrax Team names and Nicknames\n"
                    "`!fantraxroster <Team>` - Shows the Fantrax Roster for requested team. (Uses Team names or Nicknames)\n"
                    "`---- Fun Commands ----`\n"
                    "`!inform`, `!freepetey`, `!quack`, `!dops`, `!canada`, `!firegreg`, `!fuckyou`, `!petey`, `!frlg`, `!bracket`, `!playoffs`, `!pylon`, `!bolduc`, `!pride`, `!oilers`, `!gang <message>` \n")

    elif content_lower.startswith("!standings"):
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

    elif content_lower.startswith("!playerpoints"):
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

    elif content_lower.startswith("!playoffodds"):
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
            print(team_abbreviation)
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

    elif content_lower.startswith("!weekly"):
        reddit_username = "tomstoms"

        image_url = await get_latest_fantasy_hockey_image(reddit_username)

        if image_url:
            await send_embedded_image(message.channel, image_url)
        else:
            await message.channel.send("Couldn't find the latest Fantasy Hockey Schedule Summary image.")


    elif content_lower.startswith("!wj"):
        await message.channel.send("📡 Fetching World Juniors scoring leaders...")

        try:
            players_stats = await get_u20_world_juniors_stats()

            if not players_stats:
                await message.channel.send("❌ No data found from IIHF.")
                return

            print("=== World Juniors Scoring Leaders ===")
            for i, p in enumerate(players_stats, start=1):
                print(
                    f"{i}. {p['player']} ({p['team']}) "
                    f"G={p['goals']} A={p['assists']} PTS={p['points']} PIM={p['pim']}"
                )

            await message.channel.send("✅ Data fetched! Check your console for output.")
            msg = "**🏒 World Juniors Scoring Leaders (All Teams)**\n"
            for i, p in enumerate(players_stats[:25], start=1):
                msg += (
                    f"{i}. **{p['player']}** ({p['team']}) — "
                    f"{p['goals']}G {p['assists']}A {p['points']}P, {p['pim']} PIM\n"
                )

            await message.channel.send(msg)
        except Exception as e:
            await message.channel.send(f"🚨 Error fetching World Juniors data: `{e}`")

    ##Shitpost messages

    elif content_lower.startswith("!mcdavid"):
        await message.channel.send("https://www.youtube.com/watch?v=pr30MuZ23ew")

    elif content_lower.startswith("!inform"):
        await message.channel.send("'Moron' was coined in 1910 by psychologist Henry H. Goddard from the Ancient Greek word μωρός (moros), which meant 'dull' and used to describe a person with a mental age in adulthood of between 7 and 10 on the Binet scale. It was once applied to people with an intelligence quotient (IQ) of 51 to 70, being superior in one degree to 'imbecile' (IQ of 2 to 50) and superior in two degrees to 'idiot' (IQ of  to 25). The word moron, along with others including 'idiotic', 'imbecilic', 'stupid', and 'feeble-minded', was formerly considered a valid descriptor in the psychological community, but it is now deprecated in use by psychologists. Following opposition to Goddard's attempts to popularize his ideas,Goddard recanted his earlier assertions about the moron: 'It may still be objected that moron parents are likely to have imbecile or idiot children. There is not much evidence that this is the case. The danger is probably negligible.'")

    elif content_lower.startswith("!freepetey"):
        await message.channel.send("We will hold Petey hostage until our demands are met!")

    elif content_lower.startswith("!weather"):
        await message.channel.send("Crofton can experience some icy conditions")

    elif content_lower.startswith("!quack"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fsneak-peak-of-ne-anaheim-ducks-logo-v0-6eugvzi3z57d1.jpeg%3Fauto%3Dwebp%26s%3D0ebf31d88d0cbd4d591698c02f145a042e815799") 

    elif content_lower.startswith("!callme"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fnathan-mackinnon-has-received-a-five-minute-major-following-v0-81m5pd4lbcog1.jpeg%3Fwidth%3D1170%26format%3Dpjpg%26auto%3Dwebp%26s%3D4b7e3d2d74169786fbb940ef589d5364e2313b15") 

    elif content_lower.startswith("!dops"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fseth-jarvis-leaves-the-game-injured-in-ot-tripped-by-v0-2itys2bbz98g1.jpeg%3Fwidth%3D320%26crop%3Dsmart%26auto%3Dwebp%26s%3D47f03b5a3f32d481598ee02dd2486f35b52c5125") 

    elif content_lower.startswith("!canada"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fjustin-trudeau-you-cant-take-our-country-and-you-cant-take-v0-3aa23x5b8fke1.jpeg%3Fwidth%3D1080%26crop%3Dsmart%26auto%3Dwebp%26s%3D5946f29f18e5c6e235f8d28522c61bbbda84378a")

    elif content_lower.startswith("!firegreg"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fday-of-adding-things-to-a-picture-of-greg-cronin-until-he-v0-mgpst04o4tve1.jpeg%3Fwidth%3D1080%26crop%3Dsmart%26auto%3Dwebp%26s%3D24f9a46a80ea3fb2de41164425c1a60438cd1153")
    
    elif content_lower.startswith("!fireq"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fpowers-john-doe-black-ace-1s-lawyers-at-romanucci-blandin-v0-ghoedh8uklze1.jpeg%3Fwidth%3D640%26crop%3Dsmart%26auto%3Dwebp%26s%3De040aeb912fc1ea0bad5d4f89cefa782fc1650a7")

    elif content_lower.startswith("!fuckyou"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fsaturday-headlines-friedman-reports-quinn-hughes-told-the-v0-lcwyyxll347g1.jpeg%3Fauto%3Dwebp%26s%3Dd8893780aaa6505c959b444647e5dc565f4aeb4e")

    elif content_lower.startswith("!frlg"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Ffire-red-or-leaf-green-v0-7ujmn3g42u9d1.jpeg%3Fauto%3Dwebp%26s%3Db74434ceb2e8044b03485bdb4e8be477e785e3e7")

    elif content_lower.startswith("!petey"):
        await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fi.redd.it%2Foehv1qdksd621.jpg")

    elif content_lower.startswith("!oilers"):
            await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fpreview.redd.it%2Fvan-6-edm-5-paul-cotter-scores-his-second-of-the-night-to-v0-n58zj1soclsh1.png%3Fwidth%3D1672%26format%3Dpng%26auto%3Dwebp%26s%3Dff9e638d86b821fcb54beb8302abe14d8f9dd7c7")

    elif content_lower.startswith("!pride"):
            await send_embedded_image(message.channel, "https://www.reddit.com/media?url=https%3A%2F%2Fi.redd.it%2F0tp5v5i31ltg1.png")
    


    elif content_lower.startswith("!bracket"):
        await message.channel.send("https://bracketchallenge.nhl.com/en/leagues/57242 Password ape. Sign up now or be forever bedarded")

    elif content_lower.strip() in ("!playoff", "!playoffs"):
        await message.channel.send(
        "Hey everyone, its that time of year again - NHL Playoffs  meaning the yearly playoff pool. \n\n"
        "Same website as usual: https://hockeydraft.ca/ \n"
        "Login information (please be sure \"playoffs\" is checked before attempting to sign in):\n\n"
        "          Username (in honour of buffalos first playoff appearance in what 14 years?): SabreSoup\n"
        "          Password: tagethegoat \n\n"
        "When you login, to create your team, please go to the 'Entry Form' tab near the top left. From there, you will see 23 boxes of players/goalies/teams to select from. You may make one selection per box. Some boxes, such as #13 and #14, have a list of players to scroll from.  \n\n"
        "Please remember once the first game starts, there will be no changes to your team. In other words, the team you select by the time of the first playoff game will be your team for the entire playoffs. \n\n"
        "The point system can be seen at the bottom of the page of your entry form when you create your team. \n\n"
        "Buy-in is $20 paid to jmsparmar@shaw.ca - if i dont receive payment prior to the first game, i may delete your team. To make it easier on me, if you could please indicate your team name as a message that forms the etransfer, that would help me out a lot (especially for those people that i do not know lol). \n\n"
        "This year, top 3 get money (as usual) and i am reimplementing the return of $20 if you come last. \n\n"
        "As usual, feel free to pass this information along to friends and family!\n\n"
        "GOODLUCK!!!!"
    )
        
    elif content_lower.startswith("!pylon"):
        reddit_username = "tomstoms"

        image_url = "https://media1.tenor.com/m/N6xIDfjWoEUAAAAd/tyler-myers-mattias-janmark.gif"

        if image_url:
            await send_embedded_image(message.channel, image_url)
        else:
            await message.channel.send("Couldn't find the latest Fantasy Hockey Schedule Summary image.")

    elif content_lower.startswith("!bolduc"):
        reddit_username = "tomstoms"

        image_url = "https://media1.tenor.com/m/X3pYgEib-WUAAAAd/montr%C3%A9al-montreal-canadiens.gif"

        if image_url:
            await send_embedded_image(message.channel, image_url)
        else:
            await message.channel.send("Couldn't find the latest Fantasy Hockey Schedule Summary image.")

    elif content_lower.startswith("!gang "):
        quote = message.content[len("!gang "):].strip()  # Use message.content here
        
        await message.delete()

        async with aiohttp.ClientSession() as session:
            # Extract the CSRF token
            csrf_token = await get_csrf_token(session)
            
            if csrf_token:
                # Call the save_title function with the CSRF token
                url = await save_title(quote, csrf_token)
                await message.channel.send(url)
            else:
                await message.channel.send("Failed to retrieve CSRF token")

    ##Fantrax Commands

    elif content_lower.startswith("!transactions"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Only allow in bot-spam channel
        if message.channel.id not in allowed_channels:
            return

        await message.channel.send("📡 Fetching latest Fantrax transactions...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{FANTRAX_API}/transactions") as resp:
                    if resp.status != 200:
                        await message.channel.send(f"❌ Failed to contact Fantrax API (HTTP {resp.status}).")
                        return

                    data = await resp.json()

            # Handle error message from API
            if "error" in data:
                await message.channel.send(f"⚠️ {data['error']}")
                return

            transactions_list = data.get("transactions", [])[-10:]  # last 10 transactions

            if not transactions_list:
                await message.channel.send("ℹ️ No transactions found.")
                return

            embed = discord.Embed(
                title="📝 Last 10 Fantrax Transactions",
                color=discord.Color.orange()
            )

            for t in transactions_list:
                # Format each transaction
                desc = f"**Type:** {t.get('type', 'N/A')}\n"
                desc += f"**Players:** {', '.join(t.get('players', []))}\n"
                desc += f"**Teams Involved:** {', '.join(t.get('teams', []))}\n"
                desc += f"**Date:** {t.get('date', 'Unknown')}"
            
                embed.add_field(name=t.get('summary', 'Transaction'), value=desc, inline=False)

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"🚨 Error fetching transactions: `{e}`")

    elif content_lower.startswith("!fantraxteams"):

        #await message.channel.send("📡 Fetching current Fantrax teamlist...")
    
        try:
            async with aiohttp.ClientSession() as session:    
                async with session.get(f"{FANTRAX_API}/teams") as resp:
                    if resp.status != 200:
                        await message.channel.send(f"❌ Failed to contact Fantrax API (HTTP {resp.status}).")
                        return

                    data = await resp.json()
                
                    # Build the message
                    team_lines = [f"{team['name']} ({team['nickname']})" for team in data['teams']]
                    team_message = "\n".join(team_lines)

                    # Create an embed with red color
                    embed = discord.Embed(
                        title="Fantrax Team List",
                        description=team_message,
                        color=discord.Color.red()  # Red color
                    )

                    await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"🚨 Error fetching Fantrax teamlist: `{e}`")


    elif (
    content_lower == "!fantraxmatchup"
    or content_lower.startswith("!fantraxmatchup ")
):

        # Get everything after the command
        team_identifier = message.content[len("!fantraxmatchup"):].strip()

        if not team_identifier:
            await message.channel.send(
                "❌ Usage: `!fantraxmatchup <team name>` "
                "or `!fantraxmatchup all`"
            )
            return

        try:
            async with aiohttp.ClientSession() as session:

                async with session.get(
                    f"{FANTRAX_API}/matchups"
                ) as resp:

                    if resp.status != 200:
                        await message.channel.send(
                            f"❌ Failed to contact Fantrax API "
                            f"(HTTP {resp.status})."
                        )
                        return

                    data = await resp.json()

            if "error" in data:
                await message.channel.send(
                    f"❌ Fantrax error: `{data['error']}`"
                )
                return

            matchups = data.get("matchups", [])

            if not matchups:
                await message.channel.send(
                    "❌ No matchups were returned."
                )
                return

            # ----------------------------------
            # SHOW ALL MATCHUPS
            # ----------------------------------

            if team_identifier.casefold() == "all":

                matchup_lines = []

                for matchup in matchups:

                    matchup_lines.append(
                        f"**{matchup['team1']}** "
                        f"`{matchup['team1_score']}-"
                        f"{matchup['team2_score']}-"
                        f"{matchup['ties']}` "
                        f"**{matchup['team2']}**"
                    )

                embed = discord.Embed(
                    title="Fantrax Matchups",
                    description="\n".join(matchup_lines),
                    color=discord.Color.red()
                )

                embed.set_footer(
                    text=f"Scoring Period {data.get('period', '?')}"
                )

                await message.channel.send(embed=embed)
                return

            # ----------------------------------
            # FIND ONE TEAM'S MATCHUP
            # ----------------------------------

            selected_matchup = None

            for matchup in matchups:

                if (
                    team_identifier.casefold() == matchup["team1"].casefold()
                    or team_identifier.casefold() == matchup["team2"].casefold()
                ):
                    selected_matchup = matchup
                    break

            if selected_matchup is None:
                await message.channel.send(
                    f"❌ Could not find a matchup for **{team_identifier}**."
                )
                return

            # Display the matchup
            embed = discord.Embed(
                title="Fantrax Matchup",
                description=(
                    f"**{selected_matchup['team1']}** "
                    f"`{selected_matchup['team1_score']}-"
                    f"{selected_matchup['team2_score']}-"
                    f"{selected_matchup['ties']}` "
                    f"**{selected_matchup['team2']}**"
                ),
                color=discord.Color.red()
            )

            embed.set_footer(
                text=f"Scoring Period {data.get('period', '?')}"
            )

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(
                f"🚨 Error fetching Fantrax matchup: `{e}`"
            )

    elif content_lower.startswith("!fantraxroster"):

        # Normalize team names and nicknames for matching
        def normalize_team_identifier(value):
            value = unicodedata.normalize("NFKD", str(value))

            value = "".join(
                char for char in value
                if not unicodedata.combining(char)
            )

            return value.casefold().strip()

        # Get everything after !fantraxroster
        team_identifier = message.content[len("!fantraxroster"):].strip()

        if not team_identifier:
            await message.channel.send(
                "❌ Usage: `!fantraxroster <team name or abbreviation>`"
            )
            return

        try:
            async with aiohttp.ClientSession() as session:

                async with session.get(
                    f"{FANTRAX_API}/rosters",
                    params={"team": team_identifier}
                ) as resp:

                    if resp.status != 200:
                        await message.channel.send(
                            f"❌ Failed to contact Fantrax API "
                            f"(HTTP {resp.status})."
                        )
                        return

                    data = await resp.json()

            # API-level error
            if "error" in data:
                error_message = data["error"]

                if "available_teams" in data:
                    available = data["available_teams"]

                    team_lines = [
                        f"{t['name']} ({t['nickname']})"
                        for t in available
                    ]

                    await message.channel.send(
                        f"❌ {error_message}\n\n"
                        f"Available teams:\n" +
                        "\n".join(team_lines)
                    )

                else:
                    await message.channel.send(
                        f"❌ Fantrax error: `{error_message}`"
                    )

                return

            rosters = data.get("rosters", [])

            if not rosters:
                await message.channel.send(
                    "❌ No roster was returned."
                )
                return

            # Normalize the user's input
            team_identifier_normalized = normalize_team_identifier(
                team_identifier
            )

            # Find team by exact name or nickname
            roster = next(
                (
                    team for team in rosters
                    if team_identifier_normalized == normalize_team_identifier(team["name"])
                    or team_identifier_normalized == normalize_team_identifier(team["nickname"])
                ),
                None
            )

            if roster is None:

                # Dynamically list available teams
                team_lines = [
                    f"{team['name']} ({team['nickname']})"
                    for team in rosters
                ]

                await message.channel.send(
                    f"❌ Could not find a team matching **{team_identifier}**.\n\n"
                    f"**Available Teams:**\n" +
                    "\n".join(team_lines)
                )
                return

            team_name = roster["name"]
            team_nickname = roster["nickname"]
            players = roster.get("players", [])

            if not players:
                await message.channel.send(
                    f"❌ No players found on the roster for "
                    f"**{team_name} ({team_nickname})**."
                )
                return

            # Build the message
            roster_lines = []

            roster_lines.append("**Main Roster**")

            roster_lines.extend(
                f"{i}. {player}"
                for i, player in enumerate(players, 1)
            )

            roster_message = "\n".join(roster_lines)

            embed = discord.Embed(
                title=f"{team_name} Roster",
                description=roster_message,
                color=discord.Color.red()
            )

            embed.set_footer(
                text=f"Fantrax team: {team_nickname}"
            )

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(
                f"🚨 Error fetching Fantrax roster: `{e}`"
            )


    elif content_lower.startswith("!datadump"):

        try:
            async with aiohttp.ClientSession() as session:

                async with session.get(
                    f"{FANTRAX_API}/datadump"
                ) as resp:

                    if resp.status != 200:
                        await message.channel.send(
                            f"❌ Datadump failed "
                            f"(HTTP {resp.status})."
                        )
                        return

                    data = await resp.json()

            if "error" in data:
                await message.channel.send(
                    f"❌ Fantrax API error: `{data['error']}`"
                )
                return

            await message.channel.send(
                "✅ Fantrax matchup data dump complete. "
                "Check the Python console."
            )

        except Exception as e:
            await message.channel.send(
                f"🚨 Error running datadump: `{e}`"
            )







    
    
    elif content_lower.startswith("!fantraxstandings"):
        #allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Only allow in bot-spam channel
        #if message.channel.id not in allowed_channels:
        #        return

        #await message.channel.send("📡 Fetching current Fantrax standings...")

        try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{FANTRAX_API}/standings") as resp:
                        if resp.status != 200:
                            await message.channel.send(f"❌ Failed to contact Fantrax API (HTTP {resp.status}).")
                            return

                        data = await resp.json()

            # Handle error message from API
                if "error" in data:
                    await message.channel.send(f"⚠️ {data['error']}")
                    return

                standings = data.get("standings", [])
                if not standings:
                    await message.channel.send("ℹ️ No standings data found.")
                    return

                embed = discord.Embed(
                    title="🏆 Fantrax League Standings",
                    color=discord.Color.gold()
                )

                # Calculate leader points (rank 1)
                leader = standings[0]
                leader_points = ((leader.get("win", 0) * 2) + leader.get("tie", 0)) / 2

                # Loop through standings and add them to the embed
                for record in standings:
                    rank = record.get("rank", "?")
                    team = record.get("team", "Unknown")
                    win = record.get("win", 0)
                    loss = record.get("loss", 0)
                    tie = record.get("tie", 0)
                    points = ((win * 2) + tie) / 2
                    games_back = leader_points - points

                    embed.add_field(
                        name=f"#{rank} - {team}",
                        value=f"**Record:** {win}-{loss}-{tie}\n**Points:** {points}  |   **GB:** {games_back}",
                        inline=False
                    )

                await message.channel.send(embed=embed)

        except Exception as e:
                await message.channel.send(f"🚨 Error fetching Fantrax standings: `{e}`")

    elif content_lower.startswith("!matchups"):
        allowed_channels = [DISCORD_BOTSPAM_CHANNEL_ID]  # Only allow in bot-spam channel
        if message.channel.id not in allowed_channels:
            return

        await message.channel.send("📡 Fetching current Fantrax matchups...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{FANTRAX_API}/matchups") as resp:
                    if resp.status != 200:
                        await message.channel.send(f"❌ Failed to contact Fantrax API (HTTP {resp.status}).")
                        return

                    data = await resp.json()

            # Handle error message from API
            if "error" in data:
                await message.channel.send(f"⚠️ {data['error']}")
                return

            matchups = data.get("matchups", [])
            if not matchups:
                await message.channel.send("ℹ️ No current matchups found.")
                return

            embed = discord.Embed(
                title="🏒 Current Fantrax Matchups",
                color=discord.Color.blue()
            )

            # Loop through matchups and add them to the embed
            for m in matchups:
                home_team = m.get("home_team", "???")
                away_team = m.get("away_team", "???")
                home_score = m.get("home_score", "N/A")
                away_score = m.get("away_score", "N/A")
                period = m.get("period_name", "Unknown")

                embed.add_field(
                    name=f"{home_team} 🆚 {away_team}",
                    value=f"**{home_score}** - **{away_score}**\n_Period: {period}_",
                    inline=False
                )

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(f"🚨 Error fetching matchups: `{e}`")

    # Admin Override Commands (Add & Delete Channel)

    elif ADMIN_OVERRIDE:
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
    global rss_monitor_task

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
        return
        #client.loop.create_task(track_fantrax_trades())  # Start Fantrax trade tracking
    else:
        print("Fantrax integration is disabled.")

# Run the bot
client.run(TOKEN)
