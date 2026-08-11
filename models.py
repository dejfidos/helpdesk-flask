from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

db = SQLAlchemy()


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Nový")
    priority = db.Column(db.String(50), nullable=False, default="Střední")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    author = db.relationship(
        "User",
        backref="tickets"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    @property
    def created_at_local(self):
        if self.created_at is None:
            return None

        utc_time = self.created_at.replace(
            tzinfo=timezone.utc
            )

        return utc_time.astimezone(
            ZoneInfo("Europe/Prague")
        )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
