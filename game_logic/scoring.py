"""Scoring calculations for Texas 42."""


def get_count_dominoes():
    """
    Return dictionary of count dominoes and their point values.

    Count dominoes are worth extra points when captured:
    - 0-5, 1-4, 2-3: 5 points each (multiples of 5)
    - 4-6, 5-5: 10 points each (multiples of 10)
    """
    return {
        '5-0': 5,   # 0-5
        '4-1': 5,   # 1-4
        '3-2': 5,   # 2-3
        '6-4': 10,  # 4-6
        '5-5': 10,  # 5-5
    }


def calculate_trick_points(trick_dominoes):
    """
    Calculate points for a single trick.

    Args:
        trick_dominoes: List of Domino objects in the trick

    Returns:
        Total points (1 for winning + count values)
    """
    points = 1  # Each trick is worth 1 point

    count_values = get_count_dominoes()
    for domino in trick_dominoes:
        if domino.id in count_values:
            points += count_values[domino.id]

    return points


def calculate_hand_points(tricks_won, captured_dominoes):
    """
    Calculate total points for a hand.

    Args:
        tricks_won: Number of tricks won
        captured_dominoes: List of all Domino objects captured

    Returns:
        Total points for the hand (max 42)
    """
    points = tricks_won  # 1 point per trick

    count_values = get_count_dominoes()
    for domino in captured_dominoes:
        if domino.id in count_values:
            points += count_values[domino.id]

    return points


def determine_trick_winner(played_dominoes, lead_suit, trump_suit):
    """
    Determine which domino wins a trick.

    Args:
        played_dominoes: List of (position, Domino) tuples in play order
        lead_suit: The suit that was led
        trump_suit: The current trump suit

    Returns:
        (winning_position, winning_domino)
    """
    if not played_dominoes:
        return None, None

    best_position = played_dominoes[0][0]
    best_domino = played_dominoes[0][1]
    best_is_trump = best_domino.belongs_to_suit(trump_suit)

    for position, domino in played_dominoes[1:]:
        is_trump = domino.belongs_to_suit(trump_suit)

        # Trump always beats non-trump
        if is_trump and not best_is_trump:
            best_position = position
            best_domino = domino
            best_is_trump = True
            continue

        # Non-trump can't beat trump
        if best_is_trump and not is_trump:
            continue

        # Both trump or both non-trump - compare within suit
        if is_trump:
            # Compare trump values
            current_rank = get_domino_rank(domino, trump_suit)
            best_rank = get_domino_rank(best_domino, trump_suit)
            if current_rank > best_rank:
                best_position = position
                best_domino = domino
        else:
            # Must be following lead suit to win
            if domino.belongs_to_suit(lead_suit):
                current_rank = get_domino_rank(domino, lead_suit)
                best_rank = get_domino_rank(best_domino, lead_suit)
                if current_rank > best_rank:
                    best_position = position
                    best_domino = domino

    return best_position, best_domino


def get_domino_rank(domino, suit):
    """
    Get the rank of a domino when played in a given suit.

    Ranking (highest to lowest):
    - Double of the suit (e.g., 6-6 in sixes)
    - 6-X, 5-X, 4-X, 3-X, 2-X, 1-X, 0-X

    Returns:
        Rank value (higher is better)
    """
    if not domino.belongs_to_suit(suit):
        return -1

    # Double of the suit is highest
    if domino.is_double and domino.high == suit:
        return 100

    # Otherwise, rank by the other pip value
    if domino.high == suit:
        return domino.low + 1
    else:
        return domino.high + 1


def validate_bid(bid, current_high_bid):
    """
    Validate a bid.

    Args:
        bid: The bid amount (30-42, or special bids)
        current_high_bid: The current highest bid (None if first bid)

    Returns:
        (is_valid, error_message)
    """
    # Valid bids are 30-42
    if bid < 30 or bid > 42:
        return False, "Bid must be between 30 and 42"

    # Must be higher than current high bid
    if current_high_bid is not None and bid <= current_high_bid:
        return False, f"Bid must be higher than {current_high_bid}"

    return True, None


def check_game_winner(team1_marks, team2_marks, winning_marks=7):
    """
    Check if either team has won the game.

    Args:
        team1_marks: Team 1's mark count
        team2_marks: Team 2's mark count
        winning_marks: Marks needed to win (default 7)

    Returns:
        Winning team number (1 or 2) or None if no winner yet
    """
    if team1_marks >= winning_marks:
        return 1
    if team2_marks >= winning_marks:
        return 2
    return None
