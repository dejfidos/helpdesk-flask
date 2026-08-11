from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Ticket, User


app = Flask(__name__)
app.secret_key = "tajny_klic_123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///helpdesk.db"

db.init_app(app)

migrate = Migrate(app, db)




@app.route("/")
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

@app.route("/new", methods=["GET", "POST"])
def new_ticket():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        priority = request.form["priority"]

        ticket = Ticket(
            title=title,
            description=description,
            status="Nový",
            priority=priority
        )

        db.session.add(ticket)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("new_ticket.html")


@app.route("/ticket/<int:ticket_id>")
def ticket_detail(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    return render_template(
        "ticket_detail.html",
        ticket=ticket
    )


@app.route("/ticket/<int:ticket_id>/status", methods=["POST"])
def change_status(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    new_status = request.form["status"]

    ticket.status = new_status

    db.session.commit()

    return redirect(
        url_for("ticket_detail", ticket_id=ticket_id)
    )


@app.route("/ticket/<int:ticket_id>/edit", methods=["GET","POST"])
def edit_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if request.method == "POST":
        ticket.title = request.form["title"]
        ticket.description = request.form["description"]
        ticket.status = request.form["status"]
        ticket.priority = request.form["priority"]

        db.session.commit()

        return redirect(
            url_for("ticket_detail", ticket_id=ticket_id)
        )

    return render_template("edit_ticket.html", ticket=ticket)


@app.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    db.session.delete(ticket)
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
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

        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect(url_for("index"))

        return "Špatné jméno nebo heslo"

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)