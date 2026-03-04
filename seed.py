from app import app
from models import db, Student, Officer, Director, Scholarship, Application
from datetime import datetime, timedelta


def seed_users():
    with app.app_context():
        print("--- ⏳ กำลังเตรียมความพร้อม Database... ---")

        # =========================================
        # 1. เคลียร์ข้อมูลเก่า (ตามลำดับ Foreign Key)
        # =========================================
        db.session.query(Application).delete()
        db.session.query(Scholarship).delete()
        db.session.query(Student).delete()
        db.session.query(Officer).delete()
        db.session.query(Director).delete()

        # =========================================
        # 2. สร้างนักศึกษา 10 คน
        # =========================================
        faculties = [
            "คณะวิทยาศาสตร์",
            "คณะวิศวกรรมศาสตร์",
            "คณะพยาบาลศาสตร์"
        ]

        for i in range(1, 11):
            student_id = f"68113400{i:02d}"
            mock_gpax = round(2.0 + (i * 0.2), 2)
            mock_faculty = faculties[i % len(faculties)]

            # สถานะวินัย: มี / ไม่มี เท่านั้น
            disciplinary_status = "ไม่มี" if i % 4 != 0 else "มี"

            student = Student(
                student_id=student_id,
                name=f"นักศึกษา ทดสอบที่ {i}",
                email=f"student{i}@ubu.ac.th",
                faculty=mock_faculty,
                gpax=mock_gpax,
                disciplinary_status=disciplinary_status
            )

            student.set_password("stu123456")
            db.session.add(student)

        # =========================================
        # 3. สร้างเจ้าหน้าที่ และกรรมการ
        # =========================================
        for i in range(1, 6):
            officer = Officer(
                username=f"officer{i:02d}",
                name=f"เจ้าหน้าที่ {i}"
            )
            officer.set_password("off123456")

            director = Director(
                username=f"director{i:02d}",
                name=f"กรรมการ {i}"
            )
            director.set_password("dir123456")

            db.session.add_all([officer, director])

        # =========================================
        # 4. สร้างทุนการศึกษา (ทดสอบ Matching Engine)
        # =========================================
        now = datetime.now()

        scholarships = [
            Scholarship(
                name="ทุนเรียนดี (GPA > 3.5)",
                amount=20000,
                min_gpax=3.5,
                faculty_condition="ทุกคณะ",
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=30)
            ),
            Scholarship(
                name="ทุนเฉพาะทางวิศวกรรมศาสตร์",
                amount=15000,
                min_gpax=2.5,
                faculty_condition="คณะวิศวกรรมศาสตร์",
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=15)
            ),
            Scholarship(
                name="ทุนช่วยเหลือฉุกเฉิน (ปิดรับแล้ว)",
                amount=5000,
                min_gpax=2.0,
                faculty_condition="ทุกคณะ",
                start_date=now - timedelta(days=20),
                end_date=now - timedelta(days=1)
            )
        ]

        db.session.add_all(scholarships)

        # =========================================
        # 5. Commit ทั้งหมดครั้งเดียว
        # =========================================
        db.session.commit()

        print("--- ✅ Seeding Complete! ---")
        print(f"สร้าง Students: 10 คน | Scholarships: {len(scholarships)} ทุน")


if __name__ == "__main__":
    seed_users()