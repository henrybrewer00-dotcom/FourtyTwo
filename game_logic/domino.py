class Domino:
    """Represents a single domino tile with two pip values."""

    # Count dominoes and their point values
    COUNT_DOMINOES = {
        (0, 5): 5, (5, 0): 5,
        (1, 4): 5, (4, 1): 5,
        (2, 3): 5, (3, 2): 5,
        (4, 6): 10, (6, 4): 10,
        (5, 5): 10
    }

    def __init__(self, high, low):
        """
        Create a domino with two pip values.
        Convention: high >= low for consistency.
        """
        self.high = max(high, low)
        self.low = min(high, low)

    @property
    def id(self):
        """Unique identifier for the domino."""
        return f"{self.high}-{self.low}"

    @property
    def is_double(self):
        """Check if this is a double (same value on both ends)."""
        return self.high == self.low

    @property
    def pip_total(self):
        """Total pip count on the domino."""
        return self.high + self.low

    @property
    def count_value(self):
        """Point value if this is a count domino, else 0."""
        return self.COUNT_DOMINOES.get((self.high, self.low), 0)

    @property
    def is_count(self):
        """Check if this domino is a count domino (worth points)."""
        return self.count_value > 0

    def get_suits(self):
        """Return the suits (pip values) this domino belongs to."""
        if self.is_double:
            return [self.high]
        return [self.high, self.low]

    def belongs_to_suit(self, suit):
        """Check if this domino belongs to the given suit."""
        return suit in [self.high, self.low]

    def get_rank_in_suit(self, suit, trump_suit=None):
        """
        Get the rank of this domino when played in a suit.
        Higher rank = stronger domino.
        Doubles are highest in their suit.
        When comparing within a suit, higher pip total wins.
        """
        if not self.belongs_to_suit(suit):
            return -1

        # Doubles are ranked highest (7 for the double of the suit)
        if self.is_double and self.high == suit:
            return 100 + suit  # Doubles rank highest

        # For non-doubles, rank by pip total
        return self.pip_total

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'high': self.high,
            'low': self.low,
            'is_double': self.is_double,
            'count_value': self.count_value,
            'pip_total': self.pip_total
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Domino from a dictionary."""
        return cls(data['high'], data['low'])

    @classmethod
    def from_id(cls, domino_id):
        """Create a Domino from its ID string (e.g., '6-4')."""
        high, low = map(int, domino_id.split('-'))
        return cls(high, low)

    def __eq__(self, other):
        if not isinstance(other, Domino):
            return False
        return self.high == other.high and self.low == other.low

    def __hash__(self):
        return hash((self.high, self.low))

    def __repr__(self):
        return f"Domino({self.high}, {self.low})"

    def __str__(self):
        return f"[{self.high}|{self.low}]"


def create_domino_set():
    """Create a complete double-six domino set (28 tiles)."""
    dominoes = []
    for high in range(7):
        for low in range(high + 1):
            dominoes.append(Domino(high, low))
    return dominoes
