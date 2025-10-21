# reset_db.py
from app import app, db

# drop and recreate all tables safely
with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database has been reset successfully!")
