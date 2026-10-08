from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Route(db.Model):
    __tablename__ = "routes"
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(128), default="")
    path = db.Column(db.String(128), default="/")
    upstream = db.Column(db.String(256), default="")
    auth = db.Column(db.String(16), default="none")  # none|required|api-key
    rate_limit = db.Column(db.Integer, default=100)
    rate_window = db.Column(db.Integer, default=60)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AccessLog(db.Model):
    __tablename__ = "access_logs"
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"))
    user = db.Column(db.String(64), default="")
    method = db.Column(db.String(8), default="")
    path = db.Column(db.String(256), default="")
    status = db.Column(db.Integer, default=0)
    ms = db.Column(db.Integer, default=0)
    ip = db.Column(db.String(64), default="")
    at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128), default="")
    api_key = db.Column(db.String(64), default="")
    is_admin = db.Column(db.Boolean, default=False)
