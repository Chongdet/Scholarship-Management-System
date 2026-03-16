from app import app, db
from models import Scholarship, Application, Student
import random

def setup():
    with app.app_context():
        # Create Evaluation table
        db.create_all()
        print("Ensured Evaluation table exists.")

        # Find scholarship named 'asdasd'
        sch = Scholarship.query.filter_by(name='asdasd').first()
        if not sch:
            print("Could not find scholarship 'asdasd'")
            return
        
        # Take a student, e.g. the first one
        student = Student.query.first()
        if not student:
            print("No students found!")
            return

        # Check if application already exists
        app_entry = Application.query.filter_by(student_id=student.student_id, scholarship_id=sch.id).first()
        if not app_entry:
            app_id = f"APP-{random.randint(1000, 9999)}"
            app_entry = Application(
                id=app_id,
                student_id=student.student_id,
                student_name=student.name,
                scholarship_id=sch.id,
                status='interview'  # Set to interview so it shows up in director score UI
            )
            db.session.add(app_entry)
            print(f"Created application {app_id} for student {student.student_id} on scholarship {sch.name}")
        else:
            app_entry.status = 'interview'
            print(f"Updated application {app_entry.id} status to 'interview'")
        
        db.session.commit()
        print("Done setup.")

if __name__ == "__main__":
    setup()
