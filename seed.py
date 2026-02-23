from app import app
from models import db, Student, Officer, Director, Scholarship

def seed_users():
    with app.app_context():
        print("--- ⏳ กำลังเตรียมสร้างข้อมูลจำลอง... ---")

        # 1. เคลียร์ข้อมูลเก่า (ป้องกัน ID ซ้ำ)
        Student.query.delete()
        Officer.query.delete()
        Director.query.delete()
        Scholarship.query.delete() 

        # 2. สร้างนักศึกษา 10 คน
        for i in range(1, 11):
            student_id = f"68113400{i:02d}"
            s = Student(
                student_id=student_id, 
                name=f"นักศึกษา ทดสอบที่{i}", 
                email=f"student{i}@ubu.ac.th",
                faculty="คณะวิทยาศาสตร์",
                gpax=3.50
            )
            s.set_password("stu123456")
            db.session.add(s)

        # 3. สร้างเจ้าหน้าที่ 10 คน
        for i in range(1, 11):
            username = f"officer{i:02d}"
            o = Officer(username=username, name=f"เจ้าหน้าที่ ตรวจสอบที่{i}")
            o.set_password("off123456")
            db.session.add(o)

        # 4. สร้างกรรมการ 10 คน
        for i in range(1, 11):
            username = f"director{i:02d}"
            d = Director(username=username, name=f"กรรมการ พิจารณาที่{i}")
            d.set_password("dir123456")
            db.session.add(d)

        # 5. เพิ่มทุนตั้งต้น (ถ้าไม่มีทุนจะทดสอบระบบลำบาก)
        sch = Scholarship(name="ทุนเรียนดีประจำปี 2026", amount=20000)
        db.session.add(sch)

        db.session.commit()
        print("--- ✅ สร้างข้อมูลจำลองสำเร็จ! (Role ละ 10 คน) ---")

if __name__ == "__main__":
    seed_users()