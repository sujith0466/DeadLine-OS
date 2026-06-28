from app import create_app
from database.db import db
from models.intelligence import CommandLog

app = create_app()

with app.app_context():
    # create_all() is safe because it only creates tables that don't exist yet
    db.create_all()
    print("CommandLog table checked/created successfully.")
