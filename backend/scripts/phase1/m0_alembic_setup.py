import os
import sys
import re
import subprocess

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
APP_PY_PATH = os.path.join(BACKEND_DIR, 'app.py')

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=BACKEND_DIR, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR executing {cmd}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)

def main():
    print("--- Milestone 0: Alembic Setup ---")
    
    # 1. Install flask-migrate if not in requirements.txt (Assuming it's installed via pip, but let's check)
    run_cmd("pip install Flask-Migrate==4.0.5")

    # 2. Patch app.py to include flask-migrate
    with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    if "Flask-Migrate" not in content and "flask_migrate" not in content:
        # Insert import
        content = content.replace("from flask_cors import CORS", "from flask_cors import CORS\nfrom flask_migrate import Migrate")
        
        # Insert init
        init_marker = "db.init_app(app)"
        if init_marker in content:
            content = content.replace(init_marker, f"{init_marker}\n        Migrate(app, db)")
        else:
            print("Could not find db.init_app(app) in app.py!")
            sys.exit(1)
            
        # Remove db.create_all() calls
        content = re.sub(r'with app\.app_context\(\):\s+db\.create_all\(\)', 'with app.app_context():\n        pass # db.create_all() removed for Alembic', content)
        
        with open(APP_PY_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched app.py with Flask-Migrate")
    else:
        print("Flask-Migrate already in app.py")

    # 3. Initialize Alembic
    if not os.path.exists(os.path.join(BACKEND_DIR, 'migrations')):
        run_cmd("set FLASK_APP=app.py && flask db init")
        print("Initialized Alembic migrations directory")
    else:
        print("Migrations directory already exists.")

    # 4. Generate Baseline Migration for Phase 0
    run_cmd("set FLASK_APP=app.py && flask db migrate -m \"Baseline Phase 0\"")
    
    # 5. Stamp the database so it doesn't try to create tables that already exist
    run_cmd("set FLASK_APP=app.py && flask db stamp head")
    print("Baseline migration generated and database stamped.")

if __name__ == "__main__":
    main()
