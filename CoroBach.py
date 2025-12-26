from fastapi import FastAPI
import os # Import os for interacting with the operating system
from fantraxapi import FantraxAPI, FantraxException
from dotenv import load_dotenv # Import load_dotenv from dotenv for loading environment variables
from requests import Session
import sys
import io
import os
import pickle
import time
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

@app.get("/matchups")
def get_matchups():
    global api, login_success

    print("💡 /matchups endpoint called")

    try:
        if not login_success or api is None:
            return {"error": "Not logged in"}

        print("⏳ Fetching scoring periods")

        # ✅ FIX: fetch scoreboard / scoring periods, NOT goalie max
        periods = None

        for attr in ("scoreboards", "scoreboard", "scoring_periods", "schedule"):
            if hasattr(api, attr):
                periods = getattr(api, attr)
                print(f"✅ Using api.{attr}")
                break

        if periods is None:
            return {"error": "API does not expose scoring periods"}

        if not periods:
            return {"error": "No scoring periods available"}

        current_periods = [
            p for p in periods
            if getattr(p, "current", False)
        ]

        if not current_periods:
            return {"error": "No current scoring period"}

        scoreboard = current_periods[0]

        if not getattr(scoreboard, "matchups", None):
            return {"error": "No matchups available"}

        matchups_list = []

        for m in scoreboard.matchups:
            matchup_data = {
                "home_team": getattr(m.home_team, "name", "???"),
                "away_team": getattr(m.away_team, "name", "???"),
                "home_score": getattr(m, "home_score", 0),
                "away_score": getattr(m, "away_score", 0),
                "period_name": getattr(scoreboard, "name", "Current Period"),
                "complete": getattr(scoreboard, "complete", False),
                "is_playoff": getattr(scoreboard, "playoffs", False),
                "start_date": str(getattr(scoreboard, "start", "")),
                "end_date": str(getattr(scoreboard, "end", "")),
                "current": getattr(scoreboard, "current", False),
            }

            matchups_list.append(matchup_data)

        return {"matchups": matchups_list}

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
