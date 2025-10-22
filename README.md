# FHockey
Discord Bot for my Fantasy Hockey League on Fantrax



# NHL Discord Bot

A Discord bot that fetches NHL team standings, playoff odds and player stats using the NHL API and [MoneyPuck](https://moneypuck.com/predictions.htm) and currently working on integration to Fantrax custom leagues through [Fantrax Documentation by meisnate12](https://fantraxapi.kometa.wiki/en/latest/index.html). 

---

## Features

- **Team Points**: Get the current season points for any NHL team using the team's English name, French name, or abbreviation.
  - Example: `!standings Toronto Maple Leafs`, `!standings Maple Leafs de Toronto`, or `!standings TOR`
- - **Player Stats**: Get the number of goals scored by a specific player using their player ID or Last name.
  - Example: `!playerpoints 8474574` (Tyler Myers), `!playerpoints ovechkin'

---

## Setup

### Prerequisites

1. **Python 3.8**: Ensure Python is installed on your system. 3.8 is stable. Newer does not work.
2. **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications) and obtain the bot token.
3. **NHL API**: The bot uses the official NHL API to fetch data.

### Installation
 This section is not up to date.
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Discord bot token and channels as well as Fantrax information if using:
   ```env
   DISCORD_BOT_TOKEN=your-discord-bot-token-here
   DISCORD_BOTSPAM_CHANNEL_ID=your-discord-channel-id-here
   DISCORD_TRADE_CHANNEL_ID=your-discord-channel-id-here
   DISCORD_INFO_CHANNEL_ID=your-discord-channel-id-here
   FANTRAX_USERNAME=your-username-here
   FANTRAX_PASSWORD=your-password-here
   FANTRAX_LEAGUE_ID=your-league-id-here
   ```

4. Run the bot:
   ```bash
   FHockey.bat
   ```

---

## Commands

### !Test
- **`!test`**: Check if the bot is running and give the version number
  #### Example Usage

   ```
   User: !Test
   Bot: I am alive and listening! Version: 0.4.0
   ```

### !Standings
- **`!standings <query>`**

#### Query Options:
- `all` – Returns full NHL league standings sorted by points.
- `playoffs west` or `playoffs east` – Displays the current playoff picture for the Western or Eastern Conference.
- `<division>` – Retrieves standings for a specific division (Pacific, Central, Atlantic, Metropolitan).
- `<conference>` – Retrieves standings for a conference (Western, Eastern).
- `<team name or abbreviation>` – Returns the current points for a specific NHL team. See Accepted Names Table at end of README.

##### Example:
```
User: !standings all

Bot:
🏆 NHL League Standings:
1. Team A - 80 pts
2. Team B - 78 pts
...
```
### !playerpoints
- **`!goals <player_id>`**: Get the number of goals scored by the specified player.
  - Example: `!goals 8475166` (Tyler Myers) (Work in Progress)

### !playoffodds
- **`!playoffodds <query>`**
#### Query Options:
- `<team name or abbreviation>` – Returns the current points for a specific NHL team. See Accepted Names Table at end of README.

  ##### Example:
```
User: !playoffodds Flames

Bot:
Playoff odds for CGY: 9.4%
```
----
### Meme commands
-***!freepetey***

-***!quack***

-***!Canada***

-***!Firegreg***

-***!FireQ***

-***!Petey***

-***!Bracket***


-***!gang***  ***{insert text}***

-***!playoff***

---

## Example Usage

1. **Get Team Points**:
   ```
   User: !points Toronto Maple Leafs
   Bot: 🏒 Toronto Maple Leafs currently has 95 points this season!
   ```

2. **Get Player Goals**:
   ```
   User: !goals 8475166
   Bot: 🏒 Tyler Myers has scored 5 goals this season!
   ```

3. **Test Command**:
   ```
   User: !test
   Bot: I am alive and listening! Version: 0.4.0
   ```

---
## Abbreviations Table

| Abbreviation | Team Name / Variations |
|-------------|----------------------|
| ANA         | Anaheim Ducks, Ducks d'Anaheim, Ducks, Anaheim |
| BOS         | Boston Bruins, Bruins de Boston, Bruins, Boston |
| BUF         | Buffalo Sabres, Sabres de Buffalo, Sabres, Buffalo |
| CGY         | Calgary Flames, Flames de Calgary, Calgary, Flames |
| CAR         | Carolina Hurricanes, Hurricanes de la Caroline, Carolina, Hurricanes, Canes |
| CHI         | Chicago Blackhawks, Blackhawks de Chicago, Blackhawks, Chicago, Hawks |
| COL         | Colorado Avalanche, Avalanche du Colorado, Colorado, Avalanche, Avs |
| CBJ         | Columbus Blue Jackets, Blue Jackets de Columbus, Columbus, Blue Jackets, Jackets |
| DAL         | Dallas Stars, Stars de Dallas, Dallas, Stars |
| DET         | Detroit Red Wings, Red Wings de Détroit, Detroit, Red Wings, Wings |
| EDM         | Edmonton Oilers, Oilers d'Edmonton, Edmonton, Oilers |
| FLA         | Florida Panthers, Panthers de la Floride, Florida, Panthers, Cats |
| LAK         | Los Angeles Kings, Kings de Los Angeles, Los Angeles, Kings |
| MIN         | Minnesota Wild, Wild du Minnesota, Minnesota, Wild |
| MTL         | Montreal Canadiens, Canadiens de Montréal, Montreal, Canadiens, Habs |
| NSH         | Nashville Predators, Predators de Nashville, Nashville, Predators, Preds |
| NJD         | New Jersey Devils, Devils du New Jersey, New Jersey, Devils |
| NYI         | New York Islanders, Islanders de New York, Islanders, Isls |
| NYR         | New York Rangers, Rangers de New York, Rangers, Rags |
| OTT         | Ottawa Senators, Senateurs d'Ottawa, Ottawa, Senators, Sens |
| PHI         | Philadelphia Flyers, Flyers de Philadelphie, Philadelphia, Flyers |
| PIT         | Pittsburgh Penguins, Penguins de Pittsburgh, Pittsburgh, Penguins |
| SJS         | San Jose Sharks, Sharks de San Jose, San Jose, Sharks |
| SEA         | Seattle Kraken, Kraken de Seattle, Seattle |
| STL         | St. Louis Blues, Blues de Saint-Louis, St. Louis, Blues |
| TBL         | Tampa Bay Lightning, Lightning de Tampa Bay, Tampa Bay, Lightning, Bolts |
| TOR         | Toronto Maple Leafs, Maple Leafs de Toronto, Toronto, Maple Leafs, Leafs |
| UTA         | Utah Mammoth, Mammoth de l'Utah, Utah, Mammoth |
| VAN         | Vancouver Canucks, Canucks de Vancouver, Vancouver, Canucks, Nucks |
| VGK         | Vegas Golden Knights, Golden Knights de Vegas, Vegas, Golden Knights, Knights |
| WSH         | Washington Capitals, Capitals de Washington, Washington, Capitals, Caps |
| WPG         | Winnipeg Jets, Jets de Winnipeg, Jets, Winnipeg |

---

## API Endpoints Used

- **Team Standings**: `https://api-web.nhle.com/v1/standings/now`
- **Player Stats**: `https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={}`
- **Player Info**: `https://api-web.nhle.com/v1/player/{}/landing`

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [NHL API](https://gitlab.com/dword4/nhlapi) for providing the data.
- [Discord.py](https://discordpy.readthedocs.io/) for the Discord bot framework.

---

Enjoy using the NHL Discord Bot! 
```
