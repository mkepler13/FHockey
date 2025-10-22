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
