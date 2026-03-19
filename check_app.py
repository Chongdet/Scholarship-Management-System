from app import create_app
from models import db, Application, Student

app = create_app()
with app.app_context():
    stu = Student.query.filter_by(student_id='6811454005').first()
    if stu:
        apps = Application.query.filter_by(student_id=stu.student_id).all()
        for a in apps:
            print(f"App ID: {repr(a.id)}, Scholarship ID: {a.scholarship_id}, Status: {repr(a.status)}")
    else:
        print("Student 6811454005 not found.")
