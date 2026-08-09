import os
import sys
import subprocess

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def run_cmd(cmd):
    print(f"Running: {cmd}")
    # Use the python executable from the virtual environment if it exists
    env = os.environ.copy()
    env["FLASK_APP"] = "app.py"
    
    # Prepend venv scripts to PATH
    venv_scripts = os.path.join(BACKEND_DIR, '.venv', 'Scripts')
    if os.path.exists(venv_scripts):
        env["PATH"] = venv_scripts + os.pathsep + env["PATH"]

    result = subprocess.run(cmd, cwd=BACKEND_DIR, shell=True, text=True, capture_output=True, env=env)
    if result.returncode != 0:
        print(f"ERROR executing {cmd}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)
    return result.stdout

def main():
    print("--- Milestone 0: Alembic Setup (Retry) ---")
    
    flask_cmd = ".venv\\Scripts\\python -m flask" if os.path.exists(os.path.join(BACKEND_DIR, '.venv', 'Scripts', 'python.exe')) else "python -m flask"
    
    # 3. Initialize Alembic
    if not os.path.exists(os.path.join(BACKEND_DIR, 'migrations')):
        run_cmd(f"{flask_cmd} db init")
        print("Initialized Alembic migrations directory")
    else:
        print("Migrations directory already exists.")

    # 4. Generate Baseline Migration for Phase 0
    # Wait, we need to check if a migration already exists to avoid generating duplicates.
    migrations_dir = os.path.join(BACKEND_DIR, 'migrations', 'versions')
    if not os.path.exists(migrations_dir) or not os.listdir(migrations_dir):
        run_cmd(f"{flask_cmd} db migrate -m \"Baseline Phase 0\"")
        run_cmd(f"{flask_cmd} db stamp head")
        print("Baseline migration generated and database stamped.")
    else:
        print("Migrations already exist, skipping baseline generation.")

if __name__ == "__main__":
    main()
