import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'creator_os_fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///creatoros.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Database & Login Manager with app
    # Initialize Database & Login Manager with app
    from app.models import db, User, Goal
    db.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Blueprints
    from app.auth.routes import auth
    from app.dashboard.routes import dashboard
    from app.content.routes import content
    from app.settings.routes import settings
    
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(content)
    app.register_blueprint(settings)
    
    # Root redirect to landing or dashboard
    @app.route('/')
    def root():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.landing'))
        
    # Database Table Creation
    with app.app_context():
        try:
            # Check if new columns exist
            from sqlalchemy import text
            db.session.execute(text("SELECT creator_type FROM goals LIMIT 1"))
            db.session.execute(text("SELECT scheduled_date FROM contents LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.drop_all()
            except Exception:
                pass
        db.create_all()
        
    return app
