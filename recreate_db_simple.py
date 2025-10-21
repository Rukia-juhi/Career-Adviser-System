# recreate_db_simple.py
import os
from models import db
from app import app  # ensure your app creates/configures SQLALCHEMY_DATABASE_URI

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.sqlite')

print("Using DB at:", DB_PATH)
print("Dropping & recreating DB (tables only).")

# make sure app context exists and db metadata uses the same app
with app.app_context():
    # drop all (WARNING: deletes data)
    db.drop_all()
    # create all tables from models.py
    db.create_all()

print("Done. (Tables recreated)")
