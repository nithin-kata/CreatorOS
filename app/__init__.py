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

def ensure_dependencies():
    import sys
    import subprocess
    dependencies = [("pypdf", "pypdf"), ("docx", "python-docx")]
    for module_name, pip_name in dependencies:
        try:
            __import__(module_name)
        except ImportError:
            try:
                print(f"Installing missing dependency: {pip_name}...")
                subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True)
            except Exception as e:
                print(f"Failed to install {pip_name}: {e}")

def create_app():
    ensure_dependencies()
    app = Flask(__name__)
    
    # Hot-reload image copy operations
    import shutil
    dest_dir = r"c:\Users\NITHIN KATA\Downloads\Creator_Os\app\static\images"
    brain_dir = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e"
    creator_imgs = [
        ("creator_dev_cinematic_1782027111293.png",    "creator_dev_cinematic.png"),
        ("creator_design_cinematic_1782027128096.png", "creator_design_cinematic.png"),
        ("creator_writer_cinematic_1782027143962.png", "creator_writer_cinematic.png"),
        ("creator_travel_cinematic_1782027906298.png", "creator_travel_cinematic.png"),
        ("creator_fitness_cinematic_1782027920048.png","creator_fitness_cinematic.png"),
        ("creator_fashion_cinematic_1782027933436.png","creator_fashion_cinematic.png"),
        ("creator_food_cinematic_1782027952221.png",   "creator_food_cinematic.png"),
        ("creator_photography_cinematic_1782027965219.png", "creator_photography_cinematic.png"),
        ("creator_finance_cinematic_1782027978216.png","creator_finance_cinematic.png"),
    ]
    for src_name, dst_name in creator_imgs:
        src = os.path.join(brain_dir, src_name)
        if os.path.exists(src):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy(src, os.path.join(dest_dir, dst_name))

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'creator_os_fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///creatoros.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Database & Login Manager with app
    # Initialize Database & Login Manager with app
    from app.models import db, User, Goal, Document
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
