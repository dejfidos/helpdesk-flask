from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename

import os
import uuid


from models import Ticket, db, User, Comment, Attachment, TicketHistory

main = Blueprint("main", __name__)

UPLOAD_FOLDER = os.path.join("uploads")

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "pdf",
    "txt",
    "log"
}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

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

def add_history(ticket_id, action):
    history = TicketHistory(
        ticket_id=ticket_id,
        user_id=session.get("user_id"),
        action=action
    )

    db.session.add(history)


@main.route("/")
@login_required
def index():
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = Ticket.query

    if search:
        query = query.filter(
            Ticket.title.ilike(f"%{search}%")
        )

    if status:
        query = query.filter_by(status=status)

    if priority:
        query = query.filter_by(priority=priority)

    tickets = query.order_by(
        Ticket.created_at.desc()
    ).all()

    new_count = Ticket.query.filter_by(status="Nový").count()
    progress_count = Ticket.query.filter_by(status="Řeší se").count()
    done_count = Ticket.query.filter_by(status="Vyřešeno").count()

    return render_template(
        "index.html",
        tickets=tickets,
        new_count=new_count,
        progress_count=progress_count,
        done_count=done_count,
        search=search,
        selected_status=status,
        selected_priority=priority
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
        db.session.flush()

        add_history(
            ticket.id,
            "Vytvořil ticket"
        )

        db.session.commit()

        flash("Nový ticket založen.", "success")

        return redirect(url_for("main.index"))

    return render_template("new_ticket.html")


@main.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    users = User.query.order_by(User.username).all()

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        users=users
    )


@main.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
def change_status(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if session.get("role") not in ["technician", "admin"]:
        flash("Nemáš oprávnění měnit stav ticketu.", "danger")
        return redirect(
            url_for("main.ticket_detail", ticket_id=ticket.id)
        )

    new_status = request.form.get("status")
    old_status = ticket.status

    if old_status != new_status:
        ticket.status = new_status

        add_history(
            ticket.id,
            f"Změnil stav z '{old_status}' na '{new_status}'"
        )

        db.session.commit()

        flash(
            f"Stav změněn: {old_status} → {new_status}.",
            "success"
        )

    else:
        flash(
            "Stav ticketu se nezměnil.",
            "info"
        )

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket.id)
    )


@main.route("/ticket/<int:ticket_id>/edit", methods=["GET","POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if session.get("role") == "user" and ticket.user_id != session.get("user_id"):
        return "Nemáš oprávnění upravovat tento ticket.", 403

    if request.method == "POST":
        ticket.title = request.form["title"]
        ticket.description = request.form["description"]
        ticket.status = request.form["status"]
        ticket.priority = request.form["priority"]

        db.session.commit()

        flash("Ticket byl editován.", "success")

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

    flash("Ticket byl smazán.", "warning")

    return redirect(url_for("main.index"))

@main.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()

    return render_template(
        "admin_users.html",
        users=users
    )

@main.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    message = request.form["message"].strip()

    if not message:
        return redirect(
            url_for("main.ticket_detail", ticket_id=ticket.id)
        )

    comment = Comment(
        ticket_id=ticket.id,
        user_id=session["user_id"],
        message=message
    )

    db.session.add(comment)

    add_history(
        ticket.id,
        "Přidal komentář"
    )

    db.session.commit()

    flash("Komenář byl přidán.", "success")

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket.id)
    )

@main.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)

    if (
        comment.user_id != session["user_id"]
        and session.get("role") != "admin"
    ):
        flash("Nemáš oprávnění smazat tento kometář", "danger")
        return redirect(
            url_for(
                "main.ticket_detail",
                ticket_id=comment.ticket_id
            )
        )

    ticket_id = comment.ticket_id

    db.session.delete(comment)

    add_history(
        ticket_id,
        "Smazal komentář"
    )

    db.session.commit()

    flash("Komentář byl odstraněn.", "warning")

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket_id)
    )

@main.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_user_role(user_id):
    user = db.get_or_404(User, user_id)

    new_role = request.form["role"]

    allowed_roles = ["user", "technician", "admin"]

    if new_role not in allowed_roles:
        return "Neplatná role", 400

    if user.id == session["user_id"] and new_role != "admin":
        return "Nemůžeš sám sobě odebrat roli admina.", 403

    user.role = new_role
    db.session.commit()

    flash("Role byla změněna.", "success")

    return redirect(url_for("main.admin_users"))


@main.route("/ticket/<int:ticket_id>/assign", methods=["POST"])
@login_required
def assign_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if session.get("role") not in ["technician", "admin"]:
        flash("Nemáš oprávnění měnit přiřazení ticketu.", "danger")
        return redirect(
            url_for("main.ticket_detail", ticket_id=ticket.id)
        )

    # Původní přiřazení
    old_user_id = ticket.assigned_user_id
    old_user = (
        ticket.assigned_user.username
        if ticket.assigned_user
        else "Nikdo"
    )

    # Hodnota z formuláře
    assigned_user_id = request.form.get("assigned_user_id")

    if assigned_user_id:
        new_user = db.get_or_404(User, int(assigned_user_id))
        ticket.assigned_user_id = new_user.id
        new_user_name = new_user.username
    else:
        ticket.assigned_user_id = None
        new_user_name = "Nikdo"

    # Historii zapíšeme pouze při skutečné změně
    if old_user_id != ticket.assigned_user_id:
        add_history(
            ticket.id,
            f"Změnil přiřazení z '{old_user}' na '{new_user_name}'"
        )

        flash(
            f"Přiřazení změněno: {old_user} → {new_user_name}.",
            "success"
        )
    else:
        flash(
            "Přiřazení se nezměnilo.",
            "info"
        )

    db.session.commit()

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket.id)
    )


@main.route("/my-tickets")
@login_required
def my_tickets():
    user_id = session["user_id"]

    created_tickets = Ticket.query.filter_by(
        user_id=user_id
    ).order_by(Ticket.created_at.desc()).all()

    assigned_tickets = Ticket.query.filter_by(
        assigned_user_id=user_id
    ).order_by(Ticket.created_at.desc()).all()

    return render_template(
        "my_tickets.html",
        created_tickets=created_tickets,
        assigned_tickets=assigned_tickets
    )

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Uživatel již existuje.", "warning")
            return redirect(url_for("main.register"))

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Registrace proběhla úspěšně. Nyní se můžete přihlásit.", "success")
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

            flash(f"Vítej, {user.username}!", "success")
            return redirect(url_for("main.index"))

        flash("Špatné uživatelské jméno nebo heslo.", "danger")
        return redirect(url_for("main.login"))

    return render_template("login.html")


@main.route("/logout")
def logout():

    username = session.get("username")

    session.clear()

    flash(f"Uživatel {username} byl odhlášen.", "info")

    return redirect(url_for("main.login"))


@main.route("/ticket/<int:ticket_id>/attachment", methods=["POST"])
@login_required
def upload_attachment(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)

    if "file" not in request.files:
        return "Nebyl vybrán žádný soubor.", 400

    file = request.files["file"]

    if file.filename == "":
        return "Nebyl vybrán žádný soubor.", 400

    if not allowed_file(file.filename):
        return "Tento typ souboru není povolen.", 400

    original_filename = secure_filename(file.filename)

    extension = original_filename.rsplit(".", 1)[1].lower()

    stored_filename = f"{uuid.uuid4().hex}.{extension}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file.save(
        os.path.join(
            UPLOAD_FOLDER,
            stored_filename
        )
    )

    attachment = Attachment(
        ticket_id=ticket.id,
        user_id=session["user_id"],
        filename=original_filename,
        stored_filename=stored_filename
    )

    db.session.add(attachment)

    add_history(
        ticket.id,
        f"Nahrál přílohu '{attachment.filename}'"
    )

    db.session.commit()

    flash("Příloha byla nahrána.", "success")

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket.id)
    )


@main.route("/attachment/<int:attachment_id>")
@login_required
def download_attachment(attachment_id):
    attachment = db.get_or_404(Attachment, attachment_id)

    return send_from_directory(
        UPLOAD_FOLDER,
        attachment.stored_filename,
        as_attachment=True,
        download_name=attachment.filename
    )


@main.route("/attachment/<int:attachment_id>/delete", methods=["POST"])
@login_required
def delete_attachment(attachment_id):
    attachment = db.get_or_404(Attachment, attachment_id)

    if (
        attachment.user_id != session["user_id"]
        and session.get("role") != "admin"
    ):
        return "Nemáš oprávnění smazat tuto přílohu.", 403

    ticket_id = attachment.ticket_id

    file_path = os.path.join(
        UPLOAD_FOLDER,
        attachment.stored_filename
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    filename = attachment.filename

    db.session.delete(attachment)

    add_history(
        ticket_id,
        f"Smazal přílohu '{attachment.filename}'"
    )

    db.session.commit()

    flash("Příloha byla smazána.", "warning")

    return redirect(
        url_for("main.ticket_detail", ticket_id=ticket_id)
    )
