"""
GAME 42 - Texas 42 Domino Game Server
=====================================
A multiplayer Texas 42 domino game with real-time WebSocket communication.
"""

import os
import uuid
import random
import string
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from models import db, login_manager
from models.user import User
from models.game_session import GameSession
from game_logic.game import Game

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'game42-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# In-memory game storage (active games)
active_games = {}  # game_id -> Game object


# ============================================================================
# Helper Functions
# ============================================================================

def generate_guest_username():
    """Generate a random guest username."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"Guest_{suffix}"


def get_or_create_game(game_id):
    """Get game from memory or recreate from database."""
    if game_id in active_games:
        return active_games[game_id]

    # Try to load from database
    game_session = GameSession.query.filter_by(game_id=game_id).first()
    if game_session and game_session.game_state:
        game = Game.from_dict(game_session.game_state)
        active_games[game_id] = game
        return game
    return None


def save_game_state(game):
    """Save game state to database."""
    game_session = GameSession.query.filter_by(game_id=game.game_id).first()
    if game_session:
        game_session.game_state = game.to_dict()
        game_session.status = game.phase
        game_session.team1_marks = game.team1_marks
        game_session.team2_marks = game.team2_marks
        game_session.team1_points = game.team1_hand_points
        game_session.team2_points = game.team2_hand_points

        # Update players
        players_dict = {}
        for pos, player in game.players.items():
            players_dict[pos] = player.user_id
        game_session.players = players_dict
        game_session.spectators = [s[0] for s in game.spectators]


def handle_ai_turn(game_id):
    """Handle AI player turns."""
    import random
    import time

    game = active_games.get(game_id)
    if not game:
        return

    # Check if current player is AI
    current_pos = game.current_turn
    if not current_pos or current_pos not in game.players:
        return

    player = game.players[current_pos]
    if not player.is_ai:
        return

    # Small delay to make it feel more natural
    socketio.sleep(1)

    if game.phase == 'bidding':
        # AI bidding logic
        high_bid = game.high_bid or 29
        hand = player.hand

        # Calculate hand strength
        suit_counts = {}
        for domino in hand:
            for suit in [domino.high, domino.low]:
                suit_counts[suit] = suit_counts.get(suit, 0) + 1

        best_suit = max(suit_counts, key=suit_counts.get) if suit_counts else 0
        strength = suit_counts.get(best_suit, 0)

        # Decide to bid or pass
        if strength >= 4 and high_bid < 35:
            bid = min(high_bid + 1, 35)
        elif strength >= 3 and high_bid < 32:
            bid = high_bid + 1
        else:
            bid = 0  # Pass

        success, message = game.place_bid(current_pos, bid)
        if success:
            save_game_state(game)
            socketio.emit('bid_update', {
                'position': current_pos,
                'bid': bid,
                'high_bid': game.high_bid,
                'high_bidder': game.high_bidder,
                'current_bidder': game.current_bidder if game.phase == 'bidding' else None,
                'phase': game.phase,
                'message': message
            }, room=game_id)

            # Continue if still bidding and next is AI
            if game.phase == 'bidding':
                handle_ai_turn(game_id)
            elif game.phase == 'trump_selection' and game.players[game.high_bidder].is_ai:
                handle_ai_turn(game_id)

    elif game.phase == 'trump_selection':
        # AI trump selection - pick strongest suit
        hand = player.hand
        suit_counts = {}
        for domino in hand:
            for suit in [domino.high, domino.low]:
                suit_counts[suit] = suit_counts.get(suit, 0) + 1

        best_suit = max(suit_counts, key=suit_counts.get) if suit_counts else 0

        success, message = game.select_trump(current_pos, best_suit)
        if success:
            save_game_state(game)
            socketio.emit('trump_selected', {
                'trump_suit': game.trump_suit,
                'current_leader': game.current_leader,
                'phase': game.phase,
                'message': message
            }, room=game_id)

            # Continue if next player is AI
            if game.phase == 'playing':
                handle_ai_turn(game_id)

    elif game.phase == 'playing':
        # AI play logic
        hand = player.hand
        lead_suit = game.lead_suit
        trump_suit = game.trump_suit

        # Get playable dominoes
        playable = player.get_playable_dominoes(lead_suit, trump_suit)

        if playable:
            # Simple strategy: play highest if leading, follow suit otherwise
            if not game.current_trick:
                # Leading - play a strong domino
                chosen = max(playable, key=lambda d: d.pip_total)
            else:
                # Following - try to win or dump low
                chosen = playable[0]

            success, message, trick_result = game.play_domino(current_pos, chosen.id)
            if success:
                save_game_state(game)

                play_data = {
                    'position': current_pos,
                    'domino_id': chosen.id,
                    'current_trick': [(p, d.to_dict()) for p, d in game.current_trick],
                    'lead_suit': game.lead_suit,
                    'phase': game.phase
                }

                if trick_result:
                    play_data['trick_result'] = trick_result
                    play_data['team1_tricks'] = game.team1_tricks
                    play_data['team2_tricks'] = game.team2_tricks
                    play_data['team1_hand_points'] = game.team1_hand_points
                    play_data['team2_hand_points'] = game.team2_hand_points
                    play_data['team1_marks'] = game.team1_marks
                    play_data['team2_marks'] = game.team2_marks

                    if game.phase == 'finished':
                        play_data['game_over'] = True

                socketio.emit('domino_played', play_data, room=game_id)

                # Continue if next player is AI
                if game.phase == 'playing' and game.current_turn:
                    next_player = game.players.get(game.current_turn)
                    if next_player and next_player.is_ai:
                        handle_ai_turn(game_id)


# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/')
def index():
    """Redirect to lobby or auth page."""
    if current_user.is_authenticated:
        return redirect(url_for('lobby'))
    return redirect(url_for('auth'))


@app.route('/auth')
def auth():
    """Authentication page."""
    if current_user.is_authenticated:
        return redirect(url_for('lobby'))
    return render_template('auth.html')


@app.route('/api/signup', methods=['POST'])
def signup():
    """Create a new user account."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    # Validate username
    if not username or len(username) < 3 or len(username) > 20:
        return jsonify({'error': 'Username must be 3-20 characters'}), 400

    if not username.isalnum() and '_' not in username:
        return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400

    # Validate password
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Check if username exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400

    # Create user
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/signin', methods=['POST'])
def signin():
    """Sign in an existing user."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    login_user(user, remember=data.get('remember', False))
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/guest', methods=['POST'])
def guest_login():
    """Create a temporary guest account."""
    username = generate_guest_username()

    # Ensure uniqueness
    while User.query.filter_by(username=username).first():
        username = generate_guest_username()

    user = User(username=username, is_guest=True)
    user.set_password(str(uuid.uuid4()))  # Random password
    db.session.add(user)
    db.session.commit()

    login_user(user)
    session['is_guest'] = True
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Log out the current user."""
    # If guest, delete account
    if current_user.is_guest:
        db.session.delete(current_user)
        db.session.commit()

    logout_user()
    session.clear()
    return jsonify({'success': True})


@app.route('/api/user')
@login_required
def get_current_user():
    """Get current user info."""
    return jsonify({'user': current_user.to_dict()})


# ============================================================================
# Lobby Routes
# ============================================================================

@app.route('/lobby')
@login_required
def lobby():
    """Game lobby page."""
    return render_template('lobby.html')


@app.route('/api/games')
@login_required
def list_games():
    """List all public games."""
    games = GameSession.query.filter_by(is_public=True).order_by(
        GameSession.created_at.desc()
    ).all()

    game_list = []
    for game in games:
        game_dict = game.to_dict()
        # Get usernames for players
        players = game.players
        player_names = {}
        for pos, user_id in players.items():
            if user_id:
                user = User.query.get(user_id)
                if user:
                    player_names[pos] = user.username
        game_dict['player_names'] = player_names
        game_list.append(game_dict)

    return jsonify({'games': game_list})


@app.route('/api/games', methods=['POST'])
@login_required
def create_game():
    """Create a new game."""
    data = request.get_json()
    name = data.get('name', f"{current_user.username}'s Game")
    is_public = data.get('is_public', True)

    game_id = str(uuid.uuid4())[:8]

    # Create game session in database
    game_session = GameSession(
        game_id=game_id,
        name=name[:50],
        host_id=current_user.id,
        is_public=is_public
    )
    db.session.add(game_session)
    db.session.commit()

    # Create game in memory
    game = Game(game_id)
    active_games[game_id] = game

    return jsonify({'success': True, 'game_id': game_id})


# ============================================================================
# Game Routes
# ============================================================================

@app.route('/game/<game_id>')
@login_required
def game_page(game_id):
    """Game page."""
    game_session = GameSession.query.filter_by(game_id=game_id).first()
    if not game_session:
        return redirect(url_for('lobby'))
    return render_template('game.html', game_id=game_id)


@app.route('/api/games/<game_id>')
@login_required
def get_game(game_id):
    """Get game details."""
    game = get_or_create_game(game_id)
    if not game:
        game_session = GameSession.query.filter_by(game_id=game_id).first()
        if game_session:
            return jsonify(game_session.to_dict())
        return jsonify({'error': 'Game not found'}), 404

    # Find player position if in game
    position = None
    for pos, player in game.players.items():
        if player.user_id == current_user.id:
            position = pos
            break

    is_spectator = any(s[0] == current_user.id for s in game.spectators)

    if position:
        state = game.get_state_for_player(position)
        state['my_position'] = position
    elif is_spectator:
        state = game.get_state_for_spectator()
    else:
        # Not in game yet - basic info only
        state = {
            'game_id': game.game_id,
            'phase': game.phase,
            'player_count': game.player_count,
            'players': {pos: p.to_dict(hide_hand=True) for pos, p in game.players.items()},
            'team1_marks': game.team1_marks,
            'team2_marks': game.team2_marks
        }

    return jsonify(state)


# ============================================================================
# Profile Routes
# ============================================================================

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html')


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        emit('connected', {'user': current_user.to_dict()})


@socketio.on('join_game')
def handle_join_game(data):
    """Join a game room."""
    game_id = data.get('game_id')
    game = get_or_create_game(game_id)

    if not game:
        # Try to create from database entry
        game_session = GameSession.query.filter_by(game_id=game_id).first()
        if not game_session:
            emit('error', {'message': 'Game not found'})
            return
        game = Game(game_id)
        active_games[game_id] = game

    join_room(game_id)

    # Check if already in game
    for pos, player in game.players.items():
        if player.user_id == current_user.id:
            # Reconnecting
            emit('game_state', game.get_state_for_player(pos))
            emit('player_joined', {
                'position': pos,
                'username': current_user.username,
                'reconnect': True
            }, room=game_id)
            return

    # Check if spectator
    if any(s[0] == current_user.id for s in game.spectators):
        emit('game_state', game.get_state_for_spectator())
        return

    # Try to join as player
    if not game.is_full:
        success, result = game.add_player(current_user.id, current_user.username)
        if success:
            save_game_state(game)
            emit('game_state', game.get_state_for_player(result))
            emit('player_joined', {
                'position': result,
                'username': current_user.username
            }, room=game_id)
            return

    # Join as spectator
    game.add_spectator(current_user.id, current_user.username)
    save_game_state(game)
    emit('game_state', game.get_state_for_spectator())
    emit('spectator_joined', {'username': current_user.username}, room=game_id)


@socketio.on('leave_game')
def handle_leave_game(data):
    """Leave a game room."""
    game_id = data.get('game_id')
    leave_room(game_id)

    game = active_games.get(game_id)
    if game:
        # Find and remove player
        for pos, player in list(game.players.items()):
            if player.user_id == current_user.id:
                game.remove_player(pos)
                emit('player_left', {'position': pos, 'username': current_user.username}, room=game_id)
                break

        game.remove_spectator(current_user.id)
        save_game_state(game)


@socketio.on('add_bots')
def handle_add_bots(data):
    """Add AI players to fill empty slots."""
    game_id = data.get('game_id')
    game = active_games.get(game_id)

    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Add bots to empty positions
    bot_names = ['Bot_Alice', 'Bot_Bob', 'Bot_Carol', 'Bot_Dave']
    bot_num = 0
    positions = ['north', 'south', 'east', 'west']

    for pos in positions:
        if pos not in game.players:
            bot_id = -1 - bot_num  # Negative IDs for bots
            success, _ = game.add_player(bot_id, bot_names[bot_num], pos, is_ai=True)
            if success:
                emit('player_joined', {
                    'position': pos,
                    'username': bot_names[bot_num],
                    'is_bot': True
                }, room=game_id)
            bot_num += 1

    save_game_state(game)
    emit('bots_added', {'message': f'Added {bot_num} bot(s)'}, room=game_id)


@socketio.on('start_game')
def handle_start_game(data):
    """Start the game (host only)."""
    game_id = data.get('game_id')
    game = active_games.get(game_id)

    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Verify host
    game_session = GameSession.query.filter_by(game_id=game_id).first()
    if not game_session or game_session.host_id != current_user.id:
        emit('error', {'message': 'Only the host can start the game'})
        return

    success, message = game.start_game()
    if not success:
        emit('error', {'message': message})
        return

    save_game_state(game)

    # Send state to each player
    for pos, player in game.players.items():
        state = game.get_state_for_player(pos)
        state['my_position'] = pos
        emit('game_started', state, room=game_id)

    # If it's an AI's turn, make them act
    if game.phase == 'bidding':
        handle_ai_turn(game_id)


@socketio.on('place_bid')
def handle_bid(data):
    """Handle a bid."""
    game_id = data.get('game_id')
    bid = data.get('bid', 0)

    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Find player position
    position = None
    for pos, player in game.players.items():
        if player.user_id == current_user.id:
            position = pos
            break

    if not position:
        emit('error', {'message': 'You are not in this game'})
        return

    success, message = game.place_bid(position, bid)

    if not success:
        emit('error', {'message': message})
        return

    save_game_state(game)

    # Broadcast bid update
    emit('bid_update', {
        'position': position,
        'bid': bid,
        'high_bid': game.high_bid,
        'high_bidder': game.high_bidder,
        'current_bidder': game.current_bidder,
        'phase': game.phase,
        'message': message
    }, room=game_id)

    # Trigger AI turn if needed
    if game.phase == 'bidding' and game.current_bidder:
        next_player = game.players.get(game.current_bidder)
        if next_player and next_player.is_ai:
            handle_ai_turn(game_id)
    elif game.phase == 'trump_selection' and game.high_bidder:
        bid_winner = game.players.get(game.high_bidder)
        if bid_winner and bid_winner.is_ai:
            handle_ai_turn(game_id)


@socketio.on('select_trump')
def handle_trump(data):
    """Handle trump selection."""
    game_id = data.get('game_id')
    suit = data.get('suit')

    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Find player position
    position = None
    for pos, player in game.players.items():
        if player.user_id == current_user.id:
            position = pos
            break

    if not position:
        emit('error', {'message': 'You are not in this game'})
        return

    success, message = game.select_trump(position, suit)

    if not success:
        emit('error', {'message': message})
        return

    save_game_state(game)

    # Broadcast trump selection
    emit('trump_selected', {
        'trump_suit': game.trump_suit,
        'current_leader': game.current_leader,
        'phase': game.phase,
        'message': message
    }, room=game_id)

    # Trigger AI turn if needed
    if game.phase == 'playing' and game.current_leader:
        next_player = game.players.get(game.current_leader)
        if next_player and next_player.is_ai:
            handle_ai_turn(game_id)


@socketio.on('play_domino')
def handle_play(data):
    """Handle playing a domino."""
    game_id = data.get('game_id')
    domino_id = data.get('domino_id')

    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Find player position
    position = None
    for pos, player in game.players.items():
        if player.user_id == current_user.id:
            position = pos
            break

    if not position:
        emit('error', {'message': 'You are not in this game'})
        return

    success, message, trick_result = game.play_domino(position, domino_id)

    if not success:
        emit('error', {'message': message})
        return

    save_game_state(game)

    # Broadcast play
    play_data = {
        'position': position,
        'domino_id': domino_id,
        'current_trick': [(p, d.to_dict()) for p, d in game.current_trick],
        'lead_suit': game.lead_suit,
        'phase': game.phase
    }

    if trick_result:
        play_data['trick_result'] = trick_result
        play_data['team1_tricks'] = game.team1_tricks
        play_data['team2_tricks'] = game.team2_tricks
        play_data['team1_hand_points'] = game.team1_hand_points
        play_data['team2_hand_points'] = game.team2_hand_points
        play_data['team1_marks'] = game.team1_marks
        play_data['team2_marks'] = game.team2_marks

        if game.phase == Game.PHASE_FINISHED:
            play_data['game_over'] = True
            play_data['winner'] = trick_result.get('game_winner')

    emit('domino_played', play_data, room=game_id)

    # Send updated hand to the player who played
    emit('hand_update', {
        'hand': [d.to_dict() for d in game.players[position].hand]
    })

    # Trigger AI turn if needed
    if game.phase == 'playing' and game.current_turn:
        next_player = game.players.get(game.current_turn)
        if next_player and next_player.is_ai:
            handle_ai_turn(game_id)


@socketio.on('chat_message')
def handle_chat(data):
    """Handle chat message."""
    game_id = data.get('game_id')
    message = data.get('message', '').strip()

    if not message:
        return

    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # Check if spectator
    is_spectator = any(s[0] == current_user.id for s in game.spectators)

    # Check if in game
    in_game = any(p.user_id == current_user.id for p in game.players.values())

    if not in_game and not is_spectator:
        emit('error', {'message': 'You are not in this game'})
        return

    msg = game.add_chat_message(
        current_user.id,
        current_user.username,
        message,
        is_spectator
    )
    msg['timestamp'] = datetime.utcnow().isoformat()

    emit('chat_message', msg, room=game_id)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect."""
    pass  # Could implement reconnection logic here


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error='Server error'), 500


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Get local IP for network access info
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = '127.0.0.1'

    print("\n" + "=" * 50)
    print("GAME 42 - Texas 42 Domino Game")
    print("=" * 50)
    print(f"\nServer starting...")
    print(f"\nLocal access:   http://localhost:5001")
    print(f"Network access: http://{local_ip}:5001")
    print("\nShare the network address with players on your WiFi!")
    print("=" * 50 + "\n")

    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
