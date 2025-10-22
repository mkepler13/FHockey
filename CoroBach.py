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

# Load environment variables from .env file
load_dotenv()


# Load credentials from environment
FANTRAX_USERNAME = os.getenv("FANTRAX_USERNAME")
FANTRAX_PASSWORD = os.getenv("FANTRAX_PASSWORD")
FANTRAX_LEAGUE_ID = os.getenv("FANTRAX_LEAGUE_ID")

cookie_filepath = "fantraxloggedin.cookie"

# Create a session
session = Session()

# Load saved cookies if they exist
if os.path.exists(cookie_filepath):
    with open(cookie_filepath, "rb") as f:
        for cookie in pickle.load(f):
            session.cookies.set(cookie["name"], cookie["value"])
else:
    # Login with Selenium
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
        time.sleep(5)  # Wait for login to complete

        cookies = driver.get_cookies()
        with open(cookie_filepath, "wb") as cookie_file:
            pickle.dump(cookies, cookie_file)

        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])

# Initialize FantraxAPI with authenticated session
api = FantraxAPI(FANTRAX_LEAGUE_ID, session=session)

# Create a StringIO buffer to swallow unwanted prints
f = io.StringIO()
with redirect_stdout(f):
    standings = api.standings()  # current week

# Now print clean standings
def print_standings(standings):
    for rank in sorted(standings.ranks.keys()):
        record = standings.ranks[rank]
        points = record.points if record.points is not None else "N/A"
        print(f"{record.rank}. {record.team.name}: W {record.win}, L {record.loss}, T {record.tie}, Points {points}")

print_standings(standings)