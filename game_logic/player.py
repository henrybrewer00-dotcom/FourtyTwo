from game_logic.domino import Domino


class Player:
    """Represents a player in the game."""

    # Position constants
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'

    # Team assignments
    TEAM1_POSITIONS = [NORTH, SOUTH]  # Team 1: North-South
    TEAM2_POSITIONS = [EAST, WEST]    # Team 2: East-West

    # Play order (counter-clockwise from dealer's left)
    PLAY_ORDER = [NORTH, WEST, SOUTH, EAST]

    def __init__(self, user_id, username, position, is_ai=False):
        """
        Initialize a player.

        Args:
            user_id: Database user ID
            username: Display name
            position: One of NORTH, SOUTH, EAST, WEST
            is_ai: Whether this is an AI player
        """
        self.user_id = user_id
        self.username = username
        self.position = position
        self.is_ai = is_ai
        self.hand = []  # List of Domino objects
        self.current_bid = None
        self.has_passed = False

    @property
    def team(self):
        """Return team number (1 or 2) based on position."""
        if self.position in self.TEAM1_POSITIONS:
            return 1
        return 2

    @property
    def partner_position(self):
        """Return the position of this player's partner."""
        if self.position == self.NORTH:
            return self.SOUTH
        elif self.position == self.SOUTH:
            return self.NORTH
        elif self.position == self.EAST:
            return self.WEST
        else:
            return self.EAST

    def add_domino(self, domino):
        """Add a domino to the player's hand."""
        self.hand.append(domino)

    def remove_domino(self, domino):
        """Remove and return a domino from the player's hand."""
        if domino in self.hand:
            self.hand.remove(domino)
            return domino
        return None

    def has_domino(self, domino_id):
        """Check if player has a specific domino."""
        return any(d.id == domino_id for d in self.hand)

    def get_domino(self, domino_id):
        """Get a domino from hand by ID."""
        for d in self.hand:
            if d.id == domino_id:
                return d
        return None

    def get_playable_dominoes(self, lead_suit, trump_suit):
        """
        Get list of dominoes that can be legally played.

        Args:
            lead_suit: The suit that was led (None if leading)
            trump_suit: The current trump suit

        Returns:
            List of playable Domino objects
        """
        if lead_suit is None:
            # Leading - can play anything
            return list(self.hand)

        # Must follow suit if possible
        following = [d for d in self.hand if d.belongs_to_suit(lead_suit)]
        if following:
            return following

        # Can't follow suit - can play anything
        return list(self.hand)

    def can_follow_suit(self, lead_suit):
        """Check if player can follow the led suit."""
        return any(d.belongs_to_suit(lead_suit) for d in self.hand)

    def get_dominant_suit(self):
        """
        Determine the player's strongest suit for bidding.
        Returns (suit, count) tuple.
        """
        suit_counts = {}
        for domino in self.hand:
            for suit in domino.get_suits():
                suit_counts[suit] = suit_counts.get(suit, 0) + 1

        if not suit_counts:
            return None, 0

        # Find suit with most dominoes
        best_suit = max(suit_counts, key=suit_counts.get)
        return best_suit, suit_counts[best_suit]

    def calculate_hand_strength(self, suit):
        """
        Calculate hand strength if given suit is trump.
        Used for AI bidding decisions.
        """
        strength = 0
        for domino in self.hand:
            if domino.belongs_to_suit(suit):
                # Doubles are very strong
                if domino.is_double and domino.high == suit:
                    strength += 7
                else:
                    strength += 2
                # Count dominoes are valuable
                if domino.is_count:
                    strength += domino.count_value // 5
        return strength

    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.hand = []
        self.current_bid = None
        self.has_passed = False

    def to_dict(self, hide_hand=False):
        """
        Convert player to dictionary for JSON serialization.

        Args:
            hide_hand: If True, don't include hand details (for opponents)
        """
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'position': self.position,
            'team': self.team,
            'is_ai': self.is_ai,
            'hand_count': len(self.hand),
            'current_bid': self.current_bid,
            'has_passed': self.has_passed
        }
        if not hide_hand:
            data['hand'] = [d.to_dict() for d in self.hand]
        return data

    @classmethod
    def from_dict(cls, data):
        """Create a Player from a dictionary."""
        player = cls(
            user_id=data['user_id'],
            username=data['username'],
            position=data['position'],
            is_ai=data.get('is_ai', False)
        )
        if 'hand' in data:
            player.hand = [Domino.from_dict(d) for d in data['hand']]
        player.current_bid = data.get('current_bid')
        player.has_passed = data.get('has_passed', False)
        return player

    def __repr__(self):
        return f"Player({self.username}, {self.position}, hand={len(self.hand)})"
