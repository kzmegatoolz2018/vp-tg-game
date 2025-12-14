# Telegram RPG Adventure Bot

A choose-your-own-adventure style RPG bot for Telegram built with pyTelegramBotAPI.

## Features

- Interactive RPG adventure in the fantasy world of Eldoria
- Branching narrative with multiple choices and outcomes
- Inventory system to collect items
- Persistent player data using Redis
- Docker and docker-compose support for easy deployment

## Requirements

- Python 3.7+
- Redis (for persistent storage)

## Installation

### Option 1: Direct Python Execution

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram

3. Replace `YOUR_BOT_TOKEN_HERE` in `telegram_rpg_bot.py` with your actual bot token

4. Run the bot:
```bash
python telegram_rpg_bot.py
```

### Option 2: Using Docker

1. Make sure Docker and Docker Compose are installed

2. Create a `.env` file with your bot token:
```bash
cp .env.example .env
# Edit .env and replace YOUR_BOT_TOKEN_HERE with your actual token
```

3. Build and run the containers:
```bash
docker-compose up --build
```

## Game Flow

The game starts when a user sends `/start` command to the bot. The player wakes up in a mysterious village after a shipwreck and can choose from 4 initial paths:

1. Explore the forest path
2. Enter the ruins of an ancient castle
3. Talk to the village headman
4. Check inventory

Each choice leads to new scenes with descriptions and further choices, creating a branching narrative with depth of 2-3 levels minimum.

## Architecture

- `telegram_rpg_bot.py`: Main bot implementation with all game logic
- Redis: Persistent storage for player states
- Docker: Containerization for easy deployment
- Docker Compose: Multi-container orchestration

## Game Elements

- NPCs (Non-Player Characters) like the village headman and ancient guardian
- Collectible items (sword, potion, treasure, etc.)
- Puzzles to solve
- Battle system with choices to fight or flee
- Inventory management

## Extending the Bot

The code is structured to easily add:
- More narrative branches
- Combat mechanics
- Character stats system
- Database integration instead of Redis
- More complex puzzles and challenges

## Troubleshooting

- Make sure your bot token is correct
- Check that Redis is running if using Docker setup
- Verify that the bot has necessary permissions
- Check logs for any error messages

## License

This project is created for educational purposes.
