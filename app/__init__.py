import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# Initialize Login Manager and Migrate
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(config[config_name])
    
    # Initialize Database & Login Manager with app
    from app.models import db, User, Goal, Document
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
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
        
    # Database Table Creation (non-destructive)
    with app.app_context():
        db.create_all()
        
    return app

