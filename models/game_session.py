from models import db
from datetime import datetime
import json


class GameSession(db.Model):
    __tablename__ = 'game_sessions'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Game status: 'waiting', 'bidding', 'playing', 'finished'
    status = db.Column(db.String(20), default='waiting')
    is_public = db.Column(db.Boolean, default=True)

    # Players stored as JSON: {"north": user_id, "south": user_id, "east": user_id, "west": user_id}
    players_json = db.Column(db.Text, default='{}')

    # Spectators stored as JSON list of user_ids
    spectators_json = db.Column(db.Text, default='[]')

    # Scores
    team1_marks = db.Column(db.Integer, default=0)  # North-South
    team2_marks = db.Column(db.Integer, default=0)  # East-West
    team1_points = db.Column(db.Integer, default=0)
    team2_points = db.Column(db.Integer, default=0)

    # Game state stored as JSON
    game_state_json = db.Column(db.Text, default='{}')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    @property
    def players(self):
        return json.loads(self.players_json) if self.players_json else {}

    @players.setter
    def players(self, value):
        self.players_json = json.dumps(value)

    @property
    def spectators(self):
        return json.loads(self.spectators_json) if self.spectators_json else []

    @spectators.setter
    def spectators(self, value):
        self.spectators_json = json.dumps(value)

    @property
    def game_state(self):
        return json.loads(self.game_state_json) if self.game_state_json else {}

    @game_state.setter
    def game_state(self, value):
        self.game_state_json = json.dumps(value)

    @property
    def player_count(self):
        """Count of active players (not spectators)."""
        players = self.players
        return sum(1 for pos in ['north', 'south', 'east', 'west'] if players.get(pos))

    def to_dict(self):
        """Convert game session to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'name': self.name,
            'host_id': self.host_id,
            'status': self.status,
            'is_public': self.is_public,
            'players': self.players,
            'spectators': self.spectators,
            'player_count': self.player_count,
            'team1_marks': self.team1_marks,
            'team2_marks': self.team2_marks,
            'team1_points': self.team1_points,
            'team2_points': self.team2_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
