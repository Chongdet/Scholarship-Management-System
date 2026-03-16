from app import app
from models import db, Scholarship

def fix_scholarship():
    with app.app_context():
        sch = Scholarship.query.filter_by(name='Professional Nursing 2026').first()
        if sch:
            sch.faculty_condition = 'คณะพยาบาลศาสตร์'
            db.session.commit()
            print(f"Updated {sch.name}: Faculty = {sch.faculty_condition}")
        else:
            print("Scholarship not found.")

if __name__ == "__main__":
    fix_scholarship()
