from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    totp_secret = db.Column(db.Text, nullable=False)
    totp_iv = db.Column(db.String(64), nullable=False)
    key_hash = db.Column(db.String(128), nullable=False)

class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)
    iv = db.Column(db.String(64), nullable=False)
    data = db.Column(db.Text, nullable=False)
    prev_hash = db.Column(db.String(128), nullable=False)
    current_hash = db.Column(db.String(128), nullable=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user = db.Column(db.String(80))
    action = db.Column(db.String(200))
    status = db.Column(db.String(20)) # SUCESSO, FALHA, ALERTA