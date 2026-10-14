# SkyPing

Telegram weather bot powered by [Open-Meteo](https://open-meteo.com/) (free, no API key).  
Search cities, save favourites, get multi-city snapshots, and schedule daily posts for private chats, groups, and channels — in **English** or **Persian**.

## Features

- Instant weather on `/start` for a configurable default city
- City search with up to 5 geocoding matches (EN / FA names)
- Multi-day forecast (`/forecast 3 Tehran`, up to 7 days)
- Personal city list: `/add`, `/list`, `/remove`, `/all`
- Rain alerts for saved cities (`/alerts on`)
- Inline mode: type `@YourBot city` in any chat
- Daily subscriptions with per-chat time & timezone
- Metric / imperial units
- Bilingual UI — change language anytime with `/language` or the buttons under `/start`
- SQLite persistence, in-memory TTL caches, Docker-ready

## Screenshots

> _Add screenshots here once the bot is running in Telegram._

| Welcome + language | City search | Daily post |
| ------------------ | ----------- | ---------- |
| _(placeholder)_    | _(placeholder)_ | _(placeholder)_ |

## Setup

### 1. Create a bot with BotFather

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** into `.env` as `BOT_TOKEN`
4. Enable inline mode: `/setinline` → choose your bot → set a placeholder like `city name`

### 2. Getting chat / channel IDs

- **Private chat:** message [@userinfobot](https://t.me/userinfobot) or use a similar ID bot
- **Group:** add the bot, send a message, then inspect updates (or use an ID bot in the group)
- **Channel:** forward a channel post to an ID bot, or use the channel username (`@mychannel`)

### 3. Groups

1. Add SkyPing to the group
2. Promote it so it can send messages
3. Only **group admins** may change subscriptions (`/subscribe`, `/unsubscribe`, `/settime`, `/settimezone`)

### 4. Channels

1. Add SkyPing as a **channel admin** (post messages permission)
2. Set `CHANNEL_IDS` and `CHANNEL_CITIES` in `.env`
3. Daily posts use `DEFAULT_TIMEZONE` + `DEFAULT_SEND_TIME`

## Environment variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `BOT_TOKEN` | Telegram bot token (**required**) | — |
| `DEFAULT_CITY_NAME` | City shown on `/start` | `Tehran` |
| `DEFAULT_CITY_LAT` | Default latitude | `35.6892` |
| `DEFAULT_CITY_LON` | Default longitude | `51.3890` |
| `DEFAULT_TIMEZONE` | Default IANA timezone | `Asia/Tehran` |
| `DEFAULT_SEND_TIME` | Default daily time `HH:MM` | `07:30` |
| `DEFAULT_LANGUAGE` | `en` or `fa` | `en` |
| `MAX_CITIES_PER_USER` | Cap on saved cities | `10` |
| `DEFAULT_RAIN_THRESHOLD` | Default precip % for rain alerts | `60` |
| `CHANNEL_IDS` | Comma-separated channel IDs/usernames | _(empty)_ |
| `CHANNEL_CITIES` | `Name:lat:lon,...` for channel posts | _(empty)_ |
| `DB_PATH` | SQLite file path | `storage/skyping.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

Example `CHANNEL_CITIES`:

```text
Tehran:35.6892:51.3890,Isfahan:32.6539:51.6660
```

## Run locally

```bash
# Python 3.11+
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS

# Edit .env and set BOT_TOKEN
python main.py
```

## Run with Docker

```bash
cp .env.example .env
# set BOT_TOKEN in .env

docker compose up -d --build
docker compose logs -f
```

SQLite data is stored in the `./storage` volume.

## Commands

| Command | Description |
| ------- | ----------- |
| `/start` | Welcome, language buttons, default weather |
| `/weather <city>` | Search and show weather |
| `/forecast [1-7] <city>` | Multi-day forecast (default 3 days) |
| `/add <city>` | Save a city |
| `/list` | Saved cities (tap for weather) |
| `/remove` | Remove a saved city |
| `/all` | Weather for every saved city |
| `/subscribe <city>` | Daily post for that city |
| `/unsubscribe` | Stop a daily subscription |
| `/alerts on\|off` | Rain alerts for saved cities |
| `/settime HH:MM` | Daily send time (chat timezone) |
| `/settimezone <IANA>` | e.g. `Asia/Tehran` |
| `/units metric\|imperial` | Unit preference |
| `/language` | Switch English / فارسی |

In private chats you can also send a plain city name (no command).  
Inline: type `@YourBot Tehran` in any chat (enable `/setinline` in BotFather first).

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

## License

See [LICENSE](LICENSE).
