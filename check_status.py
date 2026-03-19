from app import create_app
from models import db, Scholarship
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    s = Scholarship.query.get(1)
    if s:
        print(f"Scholarship 1: {s.name}, Status: {s.status}, End Date: {s.end_date}")
        # Ensure it's 'close' for testing
        s.status = 'close'
        db.session.commit()
        print("Updated status to 'close' for testing.")
    else:
        print("Scholarship 1 not found.")
