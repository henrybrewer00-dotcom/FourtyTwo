from models import db, login_manager
from flask_login import UserMixin
import bcrypt
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Statistics
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)

    def set_password(self, password):
        """Hash and set the password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def win_rate(self):
        """Calculate win rate percentage."""
        if self.games_played == 0:
            return 0
        return round((self.games_won / self.games_played) * 100, 1)

    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'is_guest': self.is_guest,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'win_rate': self.win_rate,
            'total_marks': self.total_marks,
            'total_points': self.total_points
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
