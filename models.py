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
    category = db.Column(db.String(50), nullable=False, default="Ostatní")


    assigned_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    assigned_user = db.relationship(
            "User",
            foreign_keys=[assigned_user_id],
            backref="assigned_tickets"
        )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    author = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="created_tickets"
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

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user"
    )

class Comment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=False
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    
    message = db.Column(
        db.Text,
        nullable=False
    )
    
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        backref=db.backref(
            "comments",
            order_by="Comment.created_at"
        )
    )

    author = db.relationship(
        "User",
        backref="comments"
    )

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=False
    )

    user_id = db.Column(
            db.Integer,
            db.ForeignKey("user.id"),
            nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )        

    stored_filename = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        backref=db.backref(
            "attachments",
            order_by="Attachment.created_at"
        )
    )

    uploader = db.relationship(
        "User",
        backref="attachments"
    )

class TicketHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    action = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ticket = db.relationship(
        "Ticket",
        backref=db.backref(
            "history",
            order_by="TicketHistory.created_at"
        )
    )

    user = db.relationship(
        "User",
        backref="history_entries"
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
    