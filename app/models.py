from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goal = db.relationship('Goal', backref='user', uselist=False, cascade="all, delete-orphan")
    contents = db.relationship('Content', backref='user', lazy=True, cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='user', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('Document', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    goal = db.Column(db.String(100), nullable=False)  # Options: Get a Job, Build Personal Brand, Grow Followers, Promote Startup
    niche = db.Column(db.String(255), nullable=False)  # Comma separated lists (e.g. AI, AWS, Startups)
    platform = db.Column(db.String(50), nullable=False)  # LinkedIn, Instagram, X, Blog
    tone = db.Column(db.String(50), nullable=False)  # Professional, Storytelling, Educational, Casual
    
    # New Personalization Fields
    creator_type = db.Column(db.String(100), nullable=True)  # Student, Professional, Entrepreneur, Content Creator
    target_audience = db.Column(db.String(255), nullable=True)  # Recruiters, Developers, Customers, etc.
    weekly_commitment = db.Column(db.Integer, nullable=True, default=3)  # 1-2, 3-4, 5+ posts
    niche_details = db.Column(db.Text, nullable=True)  # Specific details about user's sub-niche/expertise

class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Clean structured JSON/text representation of drafts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.Date, nullable=True)  # Calendar scheduling date

class Activity(db.Model):
    __tablename__ = 'activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_date = db.Column(db.Date, default=date.today, nullable=False)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
