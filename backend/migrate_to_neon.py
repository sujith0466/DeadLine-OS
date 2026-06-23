import os
from sqlalchemy import text
from app import create_app
from database.db import db
import models

def migrate():
    # Force production config to use DATABASE_URL
    os.environ["FLASK_ENV"] = "production"
    app = create_app()
    
    with app.app_context():
        print(f"Connected to: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Creating all tables in Neon PostgreSQL...")
        
        # Verify connection
        try:
            db.session.execute(text("SELECT 1"))
            print("Successfully connected to Neon PostgreSQL.")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return
            
        # Create all tables
        db.create_all()
        print("Successfully created tables.")
        
        # Verify models
        tables = db.engine.table_names() if hasattr(db.engine, 'table_names') else db.inspect(db.engine).get_table_names()
        print(f"Found tables: {tables}")
        
        # Check specific models
        expected_tables = [
            "tasks", "goals", "habits", "interventions", 
            "accountability_metrics", "coach_reports", "reflection_reports"
        ]
        
        all_match = all(t in tables for t in expected_tables)
        if all_match:
            print("All expected tables successfully verified in Neon.")
        else:
            missing = [t for t in expected_tables if t not in tables]
            print(f"Missing tables: {missing}")

if __name__ == "__main__":
    migrate()
