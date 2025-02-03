# FHockey
Discord Bot for Fantasy Hockey League



# NHL Discord Bot

A Discord bot that fetches NHL team standings and player stats using the NHL API. The bot supports commands to get team points, player goals, and more. It also supports team names in both English and French, as well as team abbreviations.

---

## Features

- **Team Points**: Get the current season points for any NHL team using the team's English name, French name, or abbreviation.
  - Example: `!points Toronto Maple Leafs`, `!points Maple Leafs de Toronto`, or `!points TOR`
- **Multi-Language Support**: Works with both English and French team names.
- **Team Abbreviations**: Supports team abbreviations (e.g., `WPG` for Winnipeg Jets).

- - **Player Stats**: Get the number of goals scored by a specific player using their player ID.
  - Example: `!goals 8475166` (Tyler Myers) (DOES NOT WORK RIGHT NOW)

---

## Setup

### Prerequisites

1. **Python 3.8**: Ensure Python is installed on your system. 3.8 is stable. Newer does not work.
2. **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications) and obtain the bot token.
3. **NHL API**: The bot uses the official NHL API to fetch data.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Discord bot token:
   ```env
   DISCORD_BOT_TOKEN=your-discord-bot-token-here
   ```

4. Run the bot:
   ```bash
   python your-bot-script-name.py
   ```

---

## Commands

- **`!points <team_name>`**: Get the current season points for the specified team.
  - Example: `!points Toronto Maple Leafs`, `!points Jets de Winnipeg`, or `!points WPG`
- **`!goals <player_id>`**: Get the number of goals scored by the specified player.
  - Example: `!goals 8475166` (Tyler Myers) (Work in Progress)
- **`!test`**: Check if the bot is running.
  - Example: `!test`

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
   Bot: I am alive and listening!
   ```

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
