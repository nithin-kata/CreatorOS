import sys

try:
    from app import create_app
    from app.models import db, User, Goal, Content, Activity
    print("✓ core module imports: OK")
    
    app = create_app()
    print("✓ Flask application creation: OK")
    
    with app.app_context():
        tables = list(db.metadata.tables.keys())
        print(f"✓ SQLAlchemy model mapping: OK (found tables: {', '.join(tables)})")
        
    print("✓ CreatorOS MVP initialization verification: SUCCESSFUL")
    sys.exit(0)
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
