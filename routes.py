from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from models import Ticket, db, User

main = Blueprint("main", __name__)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.login"))

        return view(*args, **kwargs)

    return wrapped_view

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            return "Nemáš oprávnění k této akci", 403

        return view(*args, **kwargs)

    return wrapped_view

def technician_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") not in ["technician", "admin"]:
            return "Nemáš oprávnění k této akci.", 403

        return view(*args, **kwargs)

    return wrapped_view


@main.route("/")
@login_required
def index():
    tickets = Ticket.query.all()

    new_count = Ticket.query.filter_by(status="Nový").count()
    progress_count = Ticket.query.filter_by(status="Řeší se").count()
    done_count = Ticket.query.filter_by(status="Vyřešeno").count()

    return render_template(
        "index.html",
        tickets=tickets,
        new_count=new_count,
        progress_count=progress_count,
        done_count=done_count
    )


@main.route("/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        priority = request.form["priority"]

        ticket = Ticket(
            title=title,
            description=description,
            status="Nový",
            priority=priority,
            user_id=session["user_id"]
        )

        db.session.add(ticket)
        db.session.commit()

        return redirect(url_for("main.index"))

    return render_template("new_ticket.html")


@main.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    return render_template(
        "ticket_detail.html",
        ticket=ticket
    )


@main.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
@technician_required
def change_status(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    new_status = request.form["status"]

    ticket.status = new_status

    db.session.commit()

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket_id)
    )


@main.route("/ticket/<int:ticket_id>/edit", methods=["GET","POST"])
@login_required
@technician_required
def edit_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if request.method == "POST":
        ticket.title = request.form["title"]
        ticket.description = request.form["description"]
        ticket.status = request.form["status"]
        ticket.priority = request.form["priority"]

        db.session.commit()

        return redirect(
            url_for("main.ticket_detail", ticket_id=ticket_id)
        )

    return render_template("edit_ticket.html", ticket=ticket)


@main.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    db.session.delete(ticket)
    db.session.commit()

    return redirect(url_for("main.index"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Uživatel již existuje"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("main.index"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            return redirect(url_for("main.index"))

        return "Špatné jméno nebo heslo"

    return render_template("login.html")


@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))