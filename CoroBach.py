from fastapi import FastAPI
import os # Import os for interacting with the operating system
from fantraxapi import FantraxAPI, FantraxException
from dotenv import load_dotenv # Import load_dotenv from dotenv for loading environment variables
from requests import Session
#import sys
import io
import os
import pickle
import time
import re
from datetime import datetime
from requests import Session
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from fantraxapi import FantraxAPI
from contextlib import redirect_stdout
from threading import Lock
from contextlib import asynccontextmanager

VERSION = "0.5.0"


# === Initialization ===
load_dotenv() # Load environment variables from .env file
app = FastAPI()
lock = Lock()

# Load credentials from environment
FANTRAX_USERNAME = os.getenv("FANTRAX_USERNAME")
FANTRAX_PASSWORD = os.getenv("FANTRAX_PASSWORD")
FANTRAX_LEAGUE_ID = os.getenv("FANTRAX_LEAGUE_ID")

cookie_filepath = "fantraxloggedin.cookie"
session = Session() # Create a session
api = None
login_success = False

def fantrax_login():
    global session, api, login_success

    with lock:
        try:
            # Try to load cookies if they exist
            if os.path.exists(cookie_filepath):
                with open(cookie_filepath, "rb") as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        session.cookies.set(cookie["name"], cookie["value"])
            else:
                # Use Selenium to log in
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--window-size=1920,1600")
                service = Service(ChromeDriverManager().install())

                with webdriver.Chrome(service=service, options=options) as driver:
                    driver.get("https://www.fantrax.com/login")

                    username_box = WebDriverWait(driver, 10).until(
                        expected_conditions.presence_of_element_located((By.XPATH, "//input[@formcontrolname='email']"))
                    )
                    username_box.send_keys(FANTRAX_USERNAME)

                    password_box = driver.find_element(By.XPATH, "//input[@formcontrolname='password']")
                    password_box.send_keys(FANTRAX_PASSWORD)
                    password_box.send_keys(Keys.ENTER)

                    time.sleep(5)

                    cookies = driver.get_cookies()
                    with open(cookie_filepath, "wb") as cookie_file:
                        pickle.dump(cookies, cookie_file)

                    for cookie in cookies:
                        session.cookies.set(cookie["name"], cookie["value"])

            # Verify login by fetching standings
            api = FantraxAPI(FANTRAX_LEAGUE_ID, session=session)
            f = io.StringIO()
            with redirect_stdout(f):
                standings = api.standings()

            login_success = True
            return True

        except Exception as e:
            print(f"Login failed: {e}")
            login_success = False
            return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    print("Starting Fantrax service, attempting login...")
    fantrax_login()
    yield
    print("Shutting down Fantrax service.")


# === Initialize app with lifespan ===
app = FastAPI(lifespan=lifespan)

@app.get("/status")
def get_status():
    """Return login status."""
    return {"login_success": login_success}


@app.post("/relogin")
def relogin():
    """Force a new login attempt."""
    success = fantrax_login()
    return {"relogin_success": success}


@app.get("/standings")
def get_standings():
    """Return current standings if logged in."""
    if not login_success or api is None:
        return {"error": "Not logged in"}

    f = io.StringIO()
    with redirect_stdout(f):
        standings = api.standings()

    table = []
    for rank in sorted(standings.ranks.keys()):
        record = standings.ranks[rank]
        points = record.points if record.points is not None else "N/A"
        table.append({
            "rank": record.rank,
            "team": record.team.name,
            "win": record.win,
            "loss": record.loss,
            "tie": record.tie,
            "points": points
        })

    return {"standings": table}

@app.get("/rosters")
def get_rosters():
    if not login_success or api is None:
        return {"error": "Not logged in"}

    rosters = []

    position_map = {
        "206": "C",
        "203": "LW",
        "204": "RW",
        "202": "D",
        "201": "G",
        "0": "Res",
        "-1": "IR"
    }

    for team in api.teams:
        team_id = getattr(team, "team_id", None)
        if not team_id:
            continue

        team_name = getattr(team, "name", None)
        team_nickname = getattr(team, "short", None)

        try:
            roster_obj = api.roster_info(team_id)
            player_names = []

            for row in roster_obj.rows:
                if hasattr(row, "player") and row.player:
                    player_name = str(row.player)
                    pos_id = str(getattr(row, "pos_id", ""))

                    position = position_map.get(pos_id, "Unknown")

                    player_names.append(f"{player_name} - {position} ")

        except Exception as e:
            player_names = []
            print(f"⚠️ Failed to fetch roster for {team_name}: {e}")

        rosters.append({
            "team_id": team_id,
            "name": team_name,
            "nickname": team_nickname,
            "players": player_names
        })

    return {"rosters": rosters}


@app.get("/rosters2")
def get_rosters():
    if not login_success or api is None:
        return {"error": "Not logged in"}

    rosters = []

    for team in api.teams:
        team_id = getattr(team, "team_id", None)
        if not team_id:
            continue

        team_name = getattr(team, "name", None)
        team_nickname = getattr(team, "short", None)

        try:
            roster_obj = api.roster_info(team_id)

            # ==================================================
            # DEBUG: Print raw roster data to Python console
            # ==================================================
            print("\n" + "=" * 70)
            print(f"RAW FANTRAX ROSTER DATA")
            print(f"Team: {team_name}")
            print(f"Nickname: {team_nickname}")
            print(f"Team ID: {team_id}")
            print("=" * 70)

            print("\nRoster object:")
            print(repr(roster_obj))

            print("\nRoster rows:")

            player_names = []

            for i, row in enumerate(roster_obj.rows, 1):

                print(f"\n--- Row {i} ---")
                print("Raw row:")
                print(repr(row))

                # Print all available attributes on the row
                if hasattr(row, "__dict__"):
                    print("Row attributes:")
                    print(vars(row))

                # Existing working player-name logic
                if hasattr(row, "player") and row.player:
                    player_names.append(str(row.player))
                else:
                    player_names.append("Unknown Player")

            print("\n" + "=" * 70)
            print(f"END RAW ROSTER DATA: {team_name}")
            print("=" * 70 + "\n")

        except Exception as e:
            player_names = []
            print(f"⚠️ Failed to fetch roster for {team_name}: {e}")

        rosters.append({
            "team_id": team_id,
            "name": team_name,
            "nickname": team_nickname,
            "players": player_names
        })

    return {"rosters": rosters}

@app.get("/teams") 
def get_teams():
    """Return all fantasy teams in the league."""
    if not login_success or api is None:
        return {"error": "Not logged in"}

    teams = []

    # Most Fantrax wrappers expose this
    for team in api.teams:
        team_id = (
            getattr(team, "team_id", None)
            or getattr(team, "teamId", None)
            or getattr(team, "_id", None)
        )

        teams.append({
            "team_id": team_id,
            "name": team.name,
            "nickname": team.short,
        })

    return {"teams": teams}


@app.get("/matchups")
def get_matchups():
    global api, login_success

    print("💡 /matchups endpoint called")

    try:
        if not login_success or api is None:
            return {"error": "Not logged in"}

        print("⏳ Fetching Fantrax matchup data")

        # Get the existing authenticated Fantrax session
        session = getattr(api, "session", None)

        if session is None:
            session = getattr(api, "_session", None)

        if session is None:
            return {"error": "Could not find Fantrax session"}

        # Request the Schedule / Results view
        request_data = {
            "msgs": [
                {
                    "method": "getStandings",
                    "data": {
                        "leagueId": FANTRAX_LEAGUE_ID,
                        "view": "SCHEDULE"
                    }
                }
            ]
        }

        response = session.post(
            "https://www.fantrax.com/fxpa/req",
            params={
                "leagueId": FANTRAX_LEAGUE_ID
            },
            json=request_data
        )

        if response.status_code != 200:
            return {
                "error": f"Fantrax returned HTTP {response.status_code}"
            }

        raw_data = response.json()

        # Extract the actual Fantrax response
        responses = raw_data.get("responses", [])

        if not responses:
            return {"error": "Fantrax returned no response data"}

        fantrax_data = responses[0].get("data", {})

        # Get all scoring-period tables
        table_list = fantrax_data.get("tableList", [])

        if not table_list:
            return {"error": "No scoring-period tables found"}

        # Find the scoring period containing today's date.
        # We intentionally don't use displayedSelections.period:
        # the uploaded dump showed that value did not match the
        # scoring period corresponding to the current date.

        today = datetime.now().date()
        current_table = None

        for table in table_list:
            sub_caption = table.get("subCaption", "")

            # Example:
            # (Mon Nov 23, 2026 - Sun Nov 29, 2026)
            date_match = re.search(
                r"([A-Za-z]{3} [A-Za-z]{3} \d{1,2}, \d{4})"
                r"\s*[-–]\s*"
                r"([A-Za-z]{3} [A-Za-z]{3} \d{1,2}, \d{4})",
                sub_caption
            )

            if not date_match:
                continue

            try:
                start_date = datetime.strptime(
                    date_match.group(1),
                    "%a %b %d, %Y"
                ).date()

                end_date = datetime.strptime(
                    date_match.group(2),
                    "%a %b %d, %Y"
                ).date()

                if start_date <= today <= end_date:
                    current_table = table
                    break

            except ValueError:
                continue

        if current_table is None:
            available_periods = [
                {
                    "caption": table.get("caption"),
                    "dates": table.get("subCaption")
                }
                for table in table_list
            ]

            return {
                "error": f"No scoring period found for {today}",
                "available_periods": available_periods
            }

        period_name = current_table.get(
            "caption",
            "Current Scoring Period"
        )

        period_dates = current_table.get("subCaption", "")

        print(f"✅ Found {period_name} {period_dates}")

        # Extract matchup rows
        rows = current_table.get("rows", [])

        matchups_by_id = {}

        for row in rows:
            matchup_id = row.get("matchupId")

            if not matchup_id:
                continue

            fixed_cells = row.get("fixedCells", [])
            cells = row.get("cells", [])

            if not fixed_cells or len(cells) < 3:
                continue

            team_name = fixed_cells[0].get("content")

            if not team_name:
                continue

            try:
                wins = int(cells[0].get("content"))
                losses = int(cells[1].get("content"))
                ties = int(cells[2].get("content"))
            except (TypeError, ValueError):
                # Skip rows without actual matchup scores
                continue

            if matchup_id not in matchups_by_id:
                matchups_by_id[matchup_id] = []

            matchups_by_id[matchup_id].append({
                "team": team_name,
                "wins": wins,
                "losses": losses,
                "ties": ties
            })

        # Combine the two team rows belonging to each matchup
        matchups_list = []

        for matchup_id, teams in matchups_by_id.items():

            if len(teams) != 2:
                print(
                    f"⚠️ Skipping matchup {matchup_id}: "
                    f"expected 2 teams, found {len(teams)}"
                )
                continue

            team1 = teams[0]
            team2 = teams[1]

            matchup_data = {
                "team1": team1["team"],
                "team1_score": team1["wins"],

                "team2": team2["team"],
                "team2_score": team2["wins"],

                "ties": team1["ties"],
                "matchup_id": matchup_id,

                "period_name": period_name,
                "period_dates": period_dates
            }

            matchups_list.append(matchup_data)

        if not matchups_list:
            return {
                "error": "No completed matchup scores found",
                "period": period_name,
                "dates": period_dates
            }

        print(
            f"✅ Found {len(matchups_list)} matchups "
            f"for {period_name}"
        )

        for matchup in matchups_list:
            print(
                f"{matchup['team1']} "
                f"{matchup['team1_score']}-"
                f"{matchup['team2_score']}-"
                f"{matchup['ties']} "
                f"{matchup['team2']}"
            )

        return {
            "period": period_name,
            "dates": period_dates,
            "matchups": matchups_list
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {"error": str(e)}

    
@app.get("/transactions")
def get_transactions(count: int = 100):
    """Return the last transactions"""
    global api, login_success
    if not login_success or api is None:
        return {"error": "Not logged in"}

    try:
        transactions = api.transactions(count)
        tx_list = []

        for tx in transactions:
            try:
                tx_list.append({
                    "summary": getattr(tx, "summary", "Transaction"),
                    "type": getattr(tx, "type", "N/A"),
                    "players": getattr(tx, "players", []),
                    "teams": getattr(tx, "teams", []),
                    "date": str(getattr(tx, "date", "")),
                })
            except Exception as inner_e:
                print(f"⚠️ Error processing transaction: {inner_e}")

        return {"transactions": tx_list}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Internal error: {str(e)}"}



@app.get("/datadump")
def datadump():
    if not login_success or api is None:
        return {"error": "Not logged in"}

    print("\n")
    print("=" * 100)
    print("FANTRAX MATCHUP DATA DUMP")
    print("=" * 100)

    # ----------------------------------------------------------
    # OPTION 1: Try the League scoring_period_results() method
    # ----------------------------------------------------------
    print("\n")
    print("=" * 80)
    print("OPTION 1: api.scoring_period_results()")
    print("=" * 80)

    try:
        if hasattr(api, "scoring_period_results"):

            result = api.scoring_period_results(
                season=True,
                playoffs=False
            )

            print("SUCCESS")
            print("Type:", type(result))
            print("Raw result:")
            print(repr(result))

            if hasattr(result, "__dict__"):
                print("\nResult attributes:")
                print(vars(result))

            if isinstance(result, dict):
                print("\nDictionary keys:")
                print(result.keys())

                for key, value in result.items():
                    print(f"\n--- Period {key} ---")
                    print("Type:", type(value))
                    print("Value:")
                    print(repr(value))

                    if hasattr(value, "__dict__"):
                        print("Attributes:")
                        print(vars(value))

        else:
            print("api.scoring_period_results() does not exist")

    except Exception as e:
        print("FAILED:")
        print(repr(e))

    # ----------------------------------------------------------
    # OPTION 2: Try api.standings()
    # ----------------------------------------------------------
    print("\n")
    print("=" * 80)
    print("OPTION 2: api.standings()")
    print("=" * 80)

    try:
        if hasattr(api, "standings"):

            result = api.standings()

            print("SUCCESS")
            print("Type:", type(result))
            print("Raw result:")
            print(repr(result))

            if hasattr(result, "__dict__"):
                print("\nStandings attributes:")
                print(vars(result))

        else:
            print("api.standings() does not exist")

    except Exception as e:
        print("FAILED:")
        print(repr(e))

    # ----------------------------------------------------------
    # OPTION 3: Try raw Fantrax getStandings / SCHEDULE request
    # ----------------------------------------------------------
    print("\n")
    print("=" * 80)
    print("OPTION 3: RAW getStandings / SCHEDULE")
    print("=" * 80)

    try:
        session = getattr(api, "session", None)

        if session is None:
            session = getattr(api, "_session", None)

        if session is None:
            print("Could not find Fantrax session on api object")

        else:

            request_data = {
                "msgs": [
                    {
                        "method": "getStandings",
                        "data": {
                            "leagueId": FANTRAX_LEAGUE_ID,
                            "view": "SCHEDULE"
                        }
                    }
                ]
            }

            print("\nRequest:")
            print(repr(request_data))

            response = session.post(
                "https://www.fantrax.com/fxpa/req",
                params={
                    "leagueId": FANTRAX_LEAGUE_ID
                },
                json=request_data
            )

            print("\nHTTP Status:")
            print(response.status_code)

            print("\nRAW RESPONSE:")
            print(response.text)

    except Exception as e:
        print("FAILED:")
        print(repr(e))

    # ----------------------------------------------------------
    # OPTION 4: Try raw getStandings without SCHEDULE
    # ----------------------------------------------------------
    print("\n")
    print("=" * 80)
    print("OPTION 4: RAW getStandings")
    print("=" * 80)

    try:
        session = getattr(api, "session", None)

        if session is None:
            session = getattr(api, "_session", None)

        if session is None:
            print("Could not find Fantrax session on api object")

        else:

            request_data = {
                "msgs": [
                    {
                        "method": "getStandings",
                        "data": {
                            "leagueId": FANTRAX_LEAGUE_ID
                        }
                    }
                ]
            }

            print("\nRequest:")
            print(repr(request_data))

            response = session.post(
                "https://www.fantrax.com/fxpa/req",
                params={
                    "leagueId": FANTRAX_LEAGUE_ID
                },
                json=request_data
            )

            print("\nHTTP Status:")
            print(response.status_code)

            print("\nRAW RESPONSE:")
            print(response.text)

    except Exception as e:
        print("FAILED:")
        print(repr(e))

    # ----------------------------------------------------------
    # OPTION 5: Try live scoring
    # ----------------------------------------------------------
    print("\n")
    print("=" * 80)
    print("OPTION 5: RAW getLiveScoringStats")
    print("=" * 80)

    try:
        session = getattr(api, "session", None)

        if session is None:
            session = getattr(api, "_session", None)

        if session is None:
            print("Could not find Fantrax session on api object")

        else:

            request_data = {
                "msgs": [
                    {
                        "method": "getLiveScoringStats",
                        "data": {
                            "leagueId": FANTRAX_LEAGUE_ID,
                            "newView": "true"
                        }
                    }
                ]
            }

            print("\nRequest:")
            print(repr(request_data))

            response = session.post(
                "https://www.fantrax.com/fxpa/req",
                params={
                    "leagueId": FANTRAX_LEAGUE_ID
                },
                json=request_data
            )

            print("\nHTTP Status:")
            print(response.status_code)

            print("\nRAW RESPONSE:")
            print(response.text)

    except Exception as e:
        print("FAILED:")
        print(repr(e))

    print("\n")
    print("=" * 100)
    print("END FANTRAX MATCHUP DATA DUMP")
    print("=" * 100)
    print("\n")

    return {
        "status": "Data dump complete. Check the Python console."
    }
