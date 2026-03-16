from app import app
from models import db, Student

def setup_students():
    with app.app_context():
        students = Student.query.all()
        for s in students:
            # Set required fields for 100% completeness
            s.address_current = "มหาวิทยาลัยอุบลราชธานี"
            s.mobile = "0812345678"
            s.father_job = "ค้าขาย"
            s.mother_job = "รับจ้าง"
            s.housing_status = "หอพักนักศึกษา"
            s.update_completeness()
            print(f"Updated {s.student_id}: Completeness = {s.profile_completeness}%")
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    setup_students()
