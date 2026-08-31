from flask import Flask
from flask_migrate import Migrate

from models import db
from routes import main


app = Flask(__name__)

app.secret_key = "tajny_klic_123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///helpdesk.db"

db.init_app(app)

migrate = Migrate(app, db)

app.register_blueprint(main)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
        )