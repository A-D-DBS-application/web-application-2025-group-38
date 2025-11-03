import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 👉 Zorg dat Flask altijd het juiste pad gebruikt:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATES_DIR)

# Database-config
from config import Config
app.config.from_object(Config)


db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'

@app.route('/')
def home():
    return redirect(url_for('show_users'))

@app.route('/users', methods=['GET'])
def show_users():
    users = User.query.all()
    return render_template('users.html', title='Gebruikerslijst', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('name')
    if name:
        db.session.add(User(name=name))
        db.session.commit()
    return redirect(url_for('show_users'))

# 🔍 Diagnosepagina (hiermee kunnen we checken wat Flask gebruikt)
@app.route('/_diag')
def diag():
    return {
        "current_working_dir": os.getcwd(),
        "BASE_DIR": BASE_DIR,
        "TEMPLATES_DIR": TEMPLATES_DIR,
        "template_searchpath": app.jinja_loader.searchpath,
    }

if __name__ == '__main__':
    app.run(debug=True)
