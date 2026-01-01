"""Main Game class that manages game state and flow."""

import random
import uuid
from game_logic.domino import Domino, create_domino_set
from game_logic.player import Player
from game_logic.scoring import (
    determine_trick_winner, calculate_trick_points,
    validate_bid, check_game_winner, get_domino_rank
)


class Game:
    """Manages the complete state and flow of a Texas 42 game."""

    # Game phases
    PHASE_WAITING = 'waiting'
    PHASE_DEALING = 'dealing'
    PHASE_BIDDING = 'bidding'
    PHASE_TRUMP_SELECTION = 'trump_selection'
    PHASE_PLAYING = 'playing'
    PHASE_SCORING = 'scoring'
    PHASE_FINISHED = 'finished'

    # Winning marks
    WINNING_MARKS = 7

    def __init__(self, game_id=None):
        """Initialize a new game."""
        self.game_id = game_id or str(uuid.uuid4())
        self.phase = self.PHASE_WAITING
        self.players = {}  # position -> Player
        self.spectators = []  # List of (user_id, username)

        # Hand state
        self.dealer_position = None
        self.current_bidder = None
        self.high_bid = None
        self.high_bidder = None
        self.trump_suit = None
        self.bid_winner = None

        # Trick state
        self.current_leader = None
        self.current_trick = []  # List of (position, Domino)
        self.trick_number = 0
        self.lead_suit = None

        # Score tracking
        self.team1_marks = 0
        self.team2_marks = 0
        self.team1_hand_points = 0
        self.team2_hand_points = 0
        self.team1_tricks = 0
        self.team2_tricks = 0
        self.team1_captured = []  # Dominoes captured this hand
        self.team2_captured = []

        # History
        self.hand_history = []
        self.trick_history = []
        self.chat_messages = []

    @property
    def player_count(self):
        """Number of active players."""
        return len(self.players)

    @property
    def is_full(self):
        """Check if game has 4 players."""
        return self.player_count >= 4

    @property
    def current_turn(self):
        """Return position of player whose turn it is."""
        if self.phase == self.PHASE_BIDDING:
            return self.current_bidder
        elif self.phase == self.PHASE_TRUMP_SELECTION:
            return self.high_bidder
        elif self.phase == self.PHASE_PLAYING:
            return self.current_leader if not self.current_trick else self.get_next_player(self.current_trick[-1][0])
        return None

    def add_player(self, user_id, username, preferred_position=None, is_ai=False):
        """
        Add a player to the game.

        Returns:
            (success, position or error message)
        """
        if self.is_full:
            return False, "Game is full"

        # Determine position
        available = [p for p in Player.PLAY_ORDER if p not in self.players]

        if preferred_position and preferred_position in available:
            position = preferred_position
        elif available:
            position = available[0]
        else:
            return False, "No positions available"

        player = Player(user_id, username, position, is_ai)
        self.players[position] = player
        return True, position

    def remove_player(self, position):
        """Remove a player from the game."""
        if position in self.players:
            del self.players[position]
            return True
        return False

    def add_spectator(self, user_id, username):
        """Add a spectator to the game."""
        if not any(s[0] == user_id for s in self.spectators):
            self.spectators.append((user_id, username))
            return True
        return False

    def remove_spectator(self, user_id):
        """Remove a spectator from the game."""
        self.spectators = [(uid, name) for uid, name in self.spectators if uid != user_id]

    def start_game(self):
        """Start the game if we have 4 players."""
        if not self.is_full:
            return False, "Need 4 players to start"

        # Randomly select first dealer
        self.dealer_position = random.choice(Player.PLAY_ORDER)
        self.start_new_hand()
        return True, "Game started"

    def start_new_hand(self):
        """Start a new hand - deal and begin bidding."""
        # Reset hand state
        self.high_bid = None
        self.high_bidder = None
        self.trump_suit = None
        self.bid_winner = None
        self.trick_number = 0
        self.current_trick = []
        self.team1_hand_points = 0
        self.team2_hand_points = 0
        self.team1_tricks = 0
        self.team2_tricks = 0
        self.team1_captured = []
        self.team2_captured = []

        # Reset player hands
        for player in self.players.values():
            player.reset_for_new_hand()

        # Deal
        self.deal()

        # Start bidding - player to dealer's left bids first
        self.phase = self.PHASE_BIDDING
        dealer_idx = Player.PLAY_ORDER.index(self.dealer_position)
        self.current_bidder = Player.PLAY_ORDER[(dealer_idx + 1) % 4]

    def deal(self):
        """Shuffle and deal 7 dominoes to each player."""
        self.phase = self.PHASE_DEALING
        dominoes = create_domino_set()
        random.shuffle(dominoes)

        # Deal 7 to each player
        positions = Player.PLAY_ORDER
        for i, domino in enumerate(dominoes):
            player_pos = positions[i % 4]
            self.players[player_pos].add_domino(domino)

    def place_bid(self, position, bid):
        """
        Place a bid or pass.

        Args:
            position: Player position
            bid: Bid amount (30-42) or 0 to pass

        Returns:
            (success, message)
        """
        if self.phase != self.PHASE_BIDDING:
            return False, "Not in bidding phase"

        if position != self.current_bidder:
            return False, "Not your turn to bid"

        player = self.players[position]

        # Pass
        if bid == 0:
            player.has_passed = True
            return self.advance_bidding()

        # Validate bid
        is_valid, error = validate_bid(bid, self.high_bid)
        if not is_valid:
            return False, error

        # Record bid
        player.current_bid = bid
        self.high_bid = bid
        self.high_bidder = position

        return self.advance_bidding()

    def advance_bidding(self):
        """Move to next bidder or end bidding phase."""
        # Count passed players (excluding high bidder who may have also had a previous state)
        passed_count = sum(1 for p in self.players.values() if p.has_passed)

        # If 3 have passed and someone has bid, bidding ends
        if passed_count >= 3 and self.high_bidder:
            self.bid_winner = self.high_bidder
            self.phase = self.PHASE_TRUMP_SELECTION
            return True, f"Bidding complete. {self.players[self.high_bidder].username} won with {self.high_bid}"

        # If all 4 passed without a bid, dealer must bid 30
        if passed_count >= 4 and not self.high_bidder:
            self.high_bid = 30
            self.high_bidder = self.dealer_position
            self.bid_winner = self.dealer_position
            self.players[self.dealer_position].current_bid = 30
            self.phase = self.PHASE_TRUMP_SELECTION
            return True, f"All passed. Dealer forced to bid 30"

        # Move to next non-passed player
        current_idx = Player.PLAY_ORDER.index(self.current_bidder)
        for _ in range(4):
            current_idx = (current_idx + 1) % 4
            next_pos = Player.PLAY_ORDER[current_idx]
            if not self.players[next_pos].has_passed:
                self.current_bidder = next_pos
                break

        return True, "Next bidder"

    def select_trump(self, position, suit):
        """
        Select trump suit.

        Args:
            position: Player position (must be bid winner)
            suit: Trump suit (0-6)

        Returns:
            (success, message)
        """
        if self.phase != self.PHASE_TRUMP_SELECTION:
            return False, "Not in trump selection phase"

        if position != self.high_bidder:
            return False, "Only the bid winner can select trump"

        if suit < 0 or suit > 6:
            return False, "Invalid suit"

        self.trump_suit = suit
        self.phase = self.PHASE_PLAYING
        self.current_leader = self.high_bidder
        self.trick_number = 1

        return True, f"Trump is {suit}s"

    def play_domino(self, position, domino_id):
        """
        Play a domino.

        Args:
            position: Player position
            domino_id: ID of domino to play (e.g., '6-4')

        Returns:
            (success, message, trick_result)
        """
        if self.phase != self.PHASE_PLAYING:
            return False, "Not in playing phase", None

        # Determine whose turn it is
        if not self.current_trick:
            expected_turn = self.current_leader
        else:
            expected_turn = self.get_next_player(self.current_trick[-1][0])

        if position != expected_turn:
            return False, "Not your turn", None

        player = self.players[position]
        domino = player.get_domino(domino_id)

        if not domino:
            return False, "You don't have that domino", None

        # Validate the play
        if self.current_trick:
            # Must follow suit if possible
            if not domino.belongs_to_suit(self.lead_suit):
                if player.can_follow_suit(self.lead_suit):
                    return False, f"You must follow the lead suit ({self.lead_suit}s)", None

        # Play the domino
        player.remove_domino(domino)

        # Set lead suit if this is the first play
        if not self.current_trick:
            # The lead suit is the suit the leader chooses
            # Convention: use the higher pip if not trump
            if domino.belongs_to_suit(self.trump_suit):
                self.lead_suit = self.trump_suit
            else:
                self.lead_suit = domino.high

        self.current_trick.append((position, domino))

        # Check if trick is complete
        if len(self.current_trick) >= 4:
            return self.complete_trick()

        return True, "Domino played", None

    def get_next_player(self, current_position):
        """Get the next player in counter-clockwise order."""
        idx = Player.PLAY_ORDER.index(current_position)
        return Player.PLAY_ORDER[(idx + 1) % 4]

    def complete_trick(self):
        """Complete a trick and determine winner."""
        winner_pos, winning_domino = determine_trick_winner(
            self.current_trick, self.lead_suit, self.trump_suit
        )

        # Calculate points
        points = calculate_trick_points([d for _, d in self.current_trick])

        # Award to winning team
        winner = self.players[winner_pos]
        if winner.team == 1:
            self.team1_tricks += 1
            self.team1_hand_points += points
            self.team1_captured.extend([d for _, d in self.current_trick])
        else:
            self.team2_tricks += 1
            self.team2_hand_points += points
            self.team2_captured.extend([d for _, d in self.current_trick])

        # Record trick
        trick_result = {
            'trick_number': self.trick_number,
            'plays': [(p, d.to_dict()) for p, d in self.current_trick],
            'winner': winner_pos,
            'points': points,
            'lead_suit': self.lead_suit,
            'trump_suit': self.trump_suit
        }
        self.trick_history.append(trick_result)

        # Reset for next trick
        self.current_trick = []
        self.lead_suit = None
        self.current_leader = winner_pos
        self.trick_number += 1

        # Check if hand is over
        if self.trick_number > 7:
            return self.complete_hand()

        return True, f"{winner.username} wins the trick with {points} points", trick_result

    def complete_hand(self):
        """Complete a hand and calculate marks."""
        bid_team = self.players[self.bid_winner].team

        if bid_team == 1:
            made_bid = self.team1_hand_points >= self.high_bid
            if made_bid:
                self.team1_marks += 1
                result = f"Team 1 made their bid! ({self.team1_hand_points}/{self.high_bid})"
            else:
                self.team2_marks += 1
                result = f"Team 1 got set! ({self.team1_hand_points}/{self.high_bid})"
        else:
            made_bid = self.team2_hand_points >= self.high_bid
            if made_bid:
                self.team2_marks += 1
                result = f"Team 2 made their bid! ({self.team2_hand_points}/{self.high_bid})"
            else:
                self.team1_marks += 1
                result = f"Team 2 got set! ({self.team2_hand_points}/{self.high_bid})"

        # Record hand history
        hand_record = {
            'dealer': self.dealer_position,
            'bid_winner': self.bid_winner,
            'bid': self.high_bid,
            'trump': self.trump_suit,
            'team1_points': self.team1_hand_points,
            'team2_points': self.team2_hand_points,
            'made_bid': made_bid,
            'team1_marks': self.team1_marks,
            'team2_marks': self.team2_marks
        }
        self.hand_history.append(hand_record)

        # Check for game winner
        winner = check_game_winner(self.team1_marks, self.team2_marks, self.WINNING_MARKS)
        if winner:
            self.phase = self.PHASE_FINISHED
            return True, f"Game Over! Team {winner} wins!", {'game_winner': winner, 'hand_result': result}

        # Rotate dealer and start new hand
        dealer_idx = Player.PLAY_ORDER.index(self.dealer_position)
        self.dealer_position = Player.PLAY_ORDER[(dealer_idx + 1) % 4]
        self.trick_history = []
        self.start_new_hand()

        return True, result, {'hand_result': result, 'new_hand': True}

    def add_chat_message(self, user_id, username, message, is_spectator=False):
        """Add a chat message."""
        msg = {
            'user_id': user_id,
            'username': username,
            'message': message[:200],  # Limit to 200 chars
            'is_spectator': is_spectator,
            'timestamp': None  # Will be set by server
        }
        self.chat_messages.append(msg)
        if len(self.chat_messages) > 100:
            self.chat_messages = self.chat_messages[-100:]
        return msg

    def get_state_for_player(self, position):
        """Get game state visible to a specific player."""
        state = {
            'game_id': self.game_id,
            'phase': self.phase,
            'dealer': self.dealer_position,
            'current_turn': self.current_turn,
            'high_bid': self.high_bid,
            'high_bidder': self.high_bidder,
            'trump_suit': self.trump_suit,
            'trick_number': self.trick_number,
            'current_trick': [(p, d.to_dict()) for p, d in self.current_trick],
            'lead_suit': self.lead_suit,
            'team1_marks': self.team1_marks,
            'team2_marks': self.team2_marks,
            'team1_tricks': self.team1_tricks,
            'team2_tricks': self.team2_tricks,
            'team1_hand_points': self.team1_hand_points,
            'team2_hand_points': self.team2_hand_points,
            'players': {},
            'trick_history': self.trick_history[-3:],  # Last 3 tricks
        }

        # Add player info - hide other players' hands
        for pos, player in self.players.items():
            hide = pos != position
            state['players'][pos] = player.to_dict(hide_hand=hide)

        return state

    def get_state_for_spectator(self):
        """Get full game state for spectators."""
        state = self.get_state_for_player(None)
        # Spectators can see all hands
        for pos, player in self.players.items():
            state['players'][pos] = player.to_dict(hide_hand=False)
        state['is_spectator'] = True
        return state

    def to_dict(self):
        """Convert full game state to dictionary."""
        return {
            'game_id': self.game_id,
            'phase': self.phase,
            'players': {pos: p.to_dict() for pos, p in self.players.items()},
            'spectators': self.spectators,
            'dealer_position': self.dealer_position,
            'high_bid': self.high_bid,
            'high_bidder': self.high_bidder,
            'trump_suit': self.trump_suit,
            'current_trick': [(p, d.to_dict()) for p, d in self.current_trick],
            'trick_number': self.trick_number,
            'lead_suit': self.lead_suit,
            'team1_marks': self.team1_marks,
            'team2_marks': self.team2_marks,
            'team1_hand_points': self.team1_hand_points,
            'team2_hand_points': self.team2_hand_points,
            'hand_history': self.hand_history,
            'trick_history': self.trick_history
        }

    @classmethod
    def from_dict(cls, data):
        """Recreate a Game from dictionary."""
        game = cls(data['game_id'])
        game.phase = data['phase']
        game.dealer_position = data.get('dealer_position')
        game.high_bid = data.get('high_bid')
        game.high_bidder = data.get('high_bidder')
        game.trump_suit = data.get('trump_suit')
        game.trick_number = data.get('trick_number', 0)
        game.lead_suit = data.get('lead_suit')
        game.team1_marks = data.get('team1_marks', 0)
        game.team2_marks = data.get('team2_marks', 0)
        game.team1_hand_points = data.get('team1_hand_points', 0)
        game.team2_hand_points = data.get('team2_hand_points', 0)
        game.hand_history = data.get('hand_history', [])
        game.trick_history = data.get('trick_history', [])
        game.spectators = data.get('spectators', [])

        # Reconstruct players
        for pos, pdata in data.get('players', {}).items():
            game.players[pos] = Player.from_dict(pdata)

        # Reconstruct current trick
        game.current_trick = []
        for pos, ddata in data.get('current_trick', []):
            game.current_trick.append((pos, Domino.from_dict(ddata)))

        return game
