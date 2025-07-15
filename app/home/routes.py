from flask import Blueprint, render_template
from datetime import datetime

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def index():
    return render_template("index.html", year=datetime.utcnow().year)
