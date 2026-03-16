from app import app
from models import db, Student, Officer, Director, Application

def seed_users():
    with app.app_context():
        print("--- ⏳ กำลังตรวจสอบ Database... ---")

        # ข้อมูลนักศึกษาจริง
        students_data = [
            {"student_id": "6811454001", "name": "นายธนกฤต วงศ์สุวรรณ",      "email": "thanakrit.w@ubu.ac.th",    "faculty": "คณะวิศวกรรมศาสตร์",  "gpax": 3.21},
            {"student_id": "6811454002", "name": "นางสาวพิมพ์ชนก ทองดี",      "email": "pimchanok.t@ubu.ac.th",    "faculty": "คณะวิทยาศาสตร์",     "gpax": 3.56},
            {"student_id": "6811454003", "name": "นายอภิสิทธิ์ ศรีสมบูรณ์",   "email": "apisit.s@ubu.ac.th",      "faculty": "คณะบริหารศาสตร์",    "gpax": 2.89},
            {"student_id": "6811454004", "name": "นางสาวกนกวรรณ แสงจันทร์",   "email": "kanokwan.s@ubu.ac.th",    "faculty": "คณะพยาบาลศาสตร์",    "gpax": 3.78},
            {"student_id": "6811454005", "name": "นายณัฐพงษ์ ใจดี",           "email": "nattapong.j@ubu.ac.th",   "faculty": "คณะวิศวกรรมศาสตร์",  "gpax": 3.10},
            {"student_id": "6811454006", "name": "นางสาวสุภาวดี มีสุข",       "email": "supawadee.m@ubu.ac.th",   "faculty": "คณะศิลปศาสตร์",      "gpax": 3.44},
            {"student_id": "6811454007", "name": "นายวรวุฒิ ประสงค์ดี",       "email": "worawut.p@ubu.ac.th",     "faculty": "คณะวิทยาศาสตร์",     "gpax": 2.95},
            {"student_id": "6811454008", "name": "นางสาวชนิดา รุ่งเรือง",     "email": "chanida.r@ubu.ac.th",     "faculty": "คณะนิติศาสตร์",      "gpax": 3.62},
            {"student_id": "6811454009", "name": "นายปิยะพัฒน์ สุขสงวน",     "email": "piyapat.s@ubu.ac.th",     "faculty": "คณะบริหารศาสตร์",    "gpax": 3.05},
            {"student_id": "6811454010", "name": "นางสาวอารียา ดวงจันทร์",    "email": "areeya.d@ubu.ac.th",     "faculty": "คณะเภสัชศาสตร์",     "gpax": 3.88},
        ]

        added_students = 0
        for s in students_data:
            if not Student.query.filter_by(student_id=s["student_id"]).first():
                student = Student(
                    student_id=s["student_id"],
                    name=s["name"],
                    email=s["email"],
                    faculty=s["faculty"],
                    gpax=s["gpax"],
                    disciplinary_status="ไม่มี",
                )
                student.set_password("stu123456")
                db.session.add(student)
                added_students += 1

        # =========================================
        # 2. สร้างข้อมูลเจ้าหน้าที่และกรรมการ (เฉพาะที่ยังไม่มี)
        # =========================================
        added_staff = 0

        for i in range(1, 6):
            if not Officer.query.filter_by(username=f"officer{i:02d}").first():
                officer = Officer(username=f"officer{i:02d}", name=f"เจ้าหน้าที่ {i}")
                officer.set_password("off123456")
                db.session.add(officer)
                added_staff += 1

            if not Director.query.filter_by(username=f"director{i:02d}").first():
                director = Director(username=f"director{i:02d}", name=f"กรรมการ {i}")
                director.set_password("dir123456")
                db.session.add(director)
                added_staff += 1

        db.session.commit()

        if added_students == 0 and added_staff == 0:
            print("--- ✅ ข้อมูลมีอยู่แล้วในฐานข้อมูล ไม่มีการเพิ่มข้อมูลใหม่ ---")
        else:
            print(f"--- 🎉 Seeding Complete! เพิ่มนักศึกษา {added_students} คน, เจ้าหน้าที่/กรรมการ {added_staff} คน ---")

if __name__ == "__main__":
    seed_users()