"""
DeadlineOS — SQLAlchemy Database Setup
========================================
Provides a single shared `db` instance (application-level singleton)
using the Flask-SQLAlchemy extension.

All models import `db` from here — never create a second SQLAlchemy instance.
"""

from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance.
# Initialised (bound to the Flask app) inside app.py via db.init_app(app).
db = SQLAlchemy()
