from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_login import LoginManager

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///virtual_bookshelf.db"
app.config['SECRET_KEY'] = 'Hello_there, General Kenobi'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)

from routes import *

if __name__ == "__main__":
    app.run(debug=True)