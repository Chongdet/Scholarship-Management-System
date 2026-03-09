from app import app
from models import db, Student, Officer, Director, Application # เพิ่ม Application

def seed_users():
    with app.app_context():
        print("--- ⏳ กำลังล้างข้อมูลเก่าและเตรียม Database... ---")
        
        # ล้างข้อมูลเก่าออกก่อนเพื่อให้แน่ใจว่าข้อมูลใหม่จะถูกสร้าง
        db.session.query(Application).delete()
        db.session.query(Student).delete()
        db.session.query(Officer).delete()
        db.session.query(Director).delete()
        db.session.commit()

        # =========================================
        # 1. สร้างข้อมูลนักศึกษาใหม่
        # =========================================
        print("--- 📝 กำลังสร้างข้อมูลนักศึกษาจำลอง 10 คน... ---")
        faculties = ["คณะวิทยาศาสตร์", "คณะวิศวกรรมศาสตร์", "คณะพยาบาลศาสตร์"]

        for i in range(1, 11):
            student_id = f"68113400{i:02d}"
            # ใช้ชื่อ column 'gpax' ตามที่กำหนดใน models.py
            student = Student(
                student_id=student_id,
                name=f"นักศึกษา ทดสอบที่ {i}",
                email=f"student{i}@ubu.ac.th",
                faculty=faculties[i % len(faculties)],
                gpax=round(2.0 + (i * 0.2), 2),
                disciplinary_status="ไม่มี" if i % 4 != 0 else "มี",
            )
            student.set_password("stu123456")
            db.session.add(student)
        
        # =========================================
        # 2. สร้างข้อมูลเจ้าหน้าที่และกรรมการ
        # =========================================
        print("--- 📝 กำลังสร้างข้อมูลเจ้าหน้าที่และกรรมการ... ---")
        for i in range(1, 6):
            officer = Officer(username=f"officer{i:02d}", name=f"เจ้าหน้าที่ {i}")
            officer.set_password("off123456")

            director = Director(username=f"director{i:02d}", name=f"กรรมการ {i}")
            director.set_password("dir123456")

            db.session.add_all([officer, director])

        db.session.commit()
        print("--- 🎉 Seeding Complete! ข้อมูลนักศึกษาและรหัสผ่านถูกรีเซ็ตเรียบร้อย ---")

if __name__ == "__main__":
    seed_users()