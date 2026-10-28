from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class SearchQuery(db.Model):
    __tablename__ = 'search_queries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('queries', lazy=True))

class MessageMetadata(db.Model):
    __tablename__ = 'message_metadata'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger)
    chat_id = db.Column(db.BigInteger)
    chat_username = db.Column(db.String(100))
    group_name = db.Column(db.String(200))
    text = db.Column(db.Text)
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.String(50))
    link = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message_metadata.id'), nullable=False)
    search_query_id = db.Column(db.Integer, db.ForeignKey('search_queries.id'), nullable=True)
    rule_score = db.Column(db.Float)
    ml_score = db.Column(db.Float)
    final_score = db.Column(db.Float)
    reasons = db.Column(db.Text)
    is_piracy = db.Column(db.Boolean)
    
    message = db.relationship('MessageMetadata', backref=db.backref('analysis', uselist=False))

class UserReport(db.Model):
    __tablename__ = 'user_reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message_metadata.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    telegram_api_status = db.Column(db.String(200))
    
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    message = db.relationship('MessageMetadata', backref=db.backref('reports', lazy=True))

class TelegramAuth(db.Model):
    __tablename__ = 'telegram_auth'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.String(100), nullable=False)
    api_hash = db.Column(db.String(200), nullable=False)
    session_name = db.Column(db.String(100), default='telegram_session')
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PiracyRule(db.Model):
    __tablename__ = 'piracy_rules'
    id = db.Column(db.Integer, primary_key=True)
    pattern = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, default=10)
    category = db.Column(db.String(50), default='keyword') # keyword, language, extension
    is_active = db.Column(db.Boolean, default=True)
