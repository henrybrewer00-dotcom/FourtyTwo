# GAME 42 - Texas 42 Domino Game

A multiplayer Texas 42 domino trick-taking game that runs locally with real-time WebSocket communication.

## Features

- **User Authentication**: Sign up, sign in, or play as a guest
- **Game Lobby**: Browse and join public games
- **Real-time Multiplayer**: Play with friends on the same WiFi network
- **Full Texas 42 Rules**: Complete implementation of the classic domino game
- **Emoji Chat**: Chat with players using emoji reactions
- **Spectator Mode**: Watch games in progress

## Quick Start

### 1. Install Dependencies

```bash
cd game-42
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

### 3. Run the Server

```bash
python app.py
```

### 4. Play!

- Open http://localhost:5001 in your browser
- Share your network IP (shown in terminal) with friends on the same WiFi
- Create a game or join an existing one
- Play once 4 players have joined!

## How to Play Texas 42

### Overview
- 4 players in 2 teams (partners sit opposite)
- Uses a standard double-six domino set (28 tiles)
- First team to 7 marks wins

### Game Flow

1. **Deal**: Each player receives 7 dominoes
2. **Bid**: Starting left of dealer, players bid 30-42 or pass
3. **Trump Selection**: High bidder chooses trump suit (0-6)
4. **Play**: 7 tricks are played, following suit when possible
5. **Score**: Team scores points from tricks and count dominoes

### Scoring

- Each trick won = 1 point
- Count dominoes:
  - 5-0, 4-1, 3-2 = 5 points each
  - 6-4, 5-5 = 10 points each
- Total points per hand = 42
- Make your bid = earn 1 mark
- Get "set" (fail bid) = opponents earn 1 mark

## Project Structure

```
game-42/
├── app.py              # Flask server & WebSocket handlers
├── init_db.py          # Database initialization
├── requirements.txt    # Python dependencies
├── models/             # Database models
│   ├── user.py         # User authentication
│   └── game_session.py # Game state persistence
├── game_logic/         # Game rules & logic
│   ├── game.py         # Main game class
│   ├── player.py       # Player management
│   ├── domino.py       # Domino representation
│   └── scoring.py      # Score calculations
├── templates/          # HTML templates
│   ├── base.html       # Base layout
│   ├── auth.html       # Login/signup
│   ├── lobby.html      # Game lobby
│   ├── game.html       # Game board
│   └── profile.html    # User profile
└── static/
    ├── css/            # Stylesheets
    └── js/             # JavaScript
```

## Technical Details

- **Backend**: Python Flask with Flask-SocketIO
- **Frontend**: Vanilla JavaScript with WebSocket
- **Database**: SQLite (game.db)
- **Authentication**: bcrypt password hashing, Flask-Login sessions

## Network Play

The server binds to `0.0.0.0:5001`, allowing connections from any device on the local network. When you start the server, it displays both the local and network URLs:

```
Local access:   http://localhost:5001
Network access: http://192.168.x.x:5001
```

Share the network address with players on your WiFi!

## Troubleshooting

### "Module not found" errors
Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Database errors
Reset the database:
```bash
python init_db.py --reset
```

### Connection issues
- Ensure all players are on the same WiFi network
- Check firewall settings allow port 5001
- Try using the local IP shown in the terminal

## License

MIT License - Feel free to modify and share!
