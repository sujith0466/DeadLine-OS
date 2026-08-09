import os
import sys
import subprocess

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def run_cmd(cmd):
    print(f"Running: {cmd}")
    env = os.environ.copy()
    env["FLASK_APP"] = "app.py"
    
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
    print("--- Milestone 0: Alembic Migrate Runtime Models ---")
    
    flask_cmd = ".venv\\Scripts\\python -m flask" if os.path.exists(os.path.join(BACKEND_DIR, '.venv', 'Scripts', 'python.exe')) else "python -m flask"
    
    # Generate Phase 1 Migration
    run_cmd(f"{flask_cmd} db migrate -m \"Phase 1 Runtime Models\"")
    
    # Upgrade DB
    run_cmd(f"{flask_cmd} db upgrade")
    print("Phase 1 Runtime Models migrated successfully.")

if __name__ == "__main__":
    main()
