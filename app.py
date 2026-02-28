from flask import Flask, redirect, url_for, render_template
from routes.director_routes import director_bp
from routes.officer_routes import officer_bp
from routes.student_routes import student_bp

# 1. นำเข้า db และ Models (ต้องสร้างไฟล์ models.py ไว้ด้วย)
from models import db, Scholarship, Criterion, Application
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here-change-in-production"

# 2. ตั้งค่า Database (SQLite)
# สร้างไฟล์ชื่อ scholarship.db ไว้ในโฟลเดอร์โครงการ
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "scholarship.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 3. เริ่มต้นใช้งาน Database ร่วมกับ App
db.init_app(app)

# 4. ลงทะเบียน Blueprint
app.register_blueprint(director_bp, url_prefix="/director")
app.register_blueprint(officer_bp, url_prefix="/officer")
app.register_blueprint(student_bp, url_prefix="/student")

# 5. สร้าง Database และข้อมูลจำลอง (จะทำเฉพาะตอนรันครั้งแรก)
with app.app_context():
    db.drop_all()  # ล้างตารางเดิม (ถ้ามี)
    db.create_all()  # สร้างตารางใหม่

    # 1. สร้างรายชื่อทุน (Scholarships)
    sch1 = Scholarship(scholarship_id="SCH-001", scholarship_name="ทุนอาหารกลางวัน")
    sch2 = Scholarship(scholarship_id="SCH-002", scholarship_name="ทุนเรียนดี (GPA สูง)")
    sch3 = Scholarship(scholarship_id="SCH-003", scholarship_name="ทุนกิจกรรมเด่น")
    db.session.add_all([sch1, sch2, sch3])
    db.session.commit()

    # 2. สร้างเกณฑ์คะแนนแยกตามทุน (Criteria)
    # เกณฑ์สำหรับทุนอาหารกลางวัน
    db.session.add_all(
        [
            Criterion(name="สถานะความขาดแคลน", max_score=50, scholarship_id=sch1.scholarship_id),
            Criterion(name="ความประพฤติ", max_score=30, scholarship_id=sch1.scholarship_id),
            Criterion(name="สัมภาษณ์", max_score=20, scholarship_id=sch1.scholarship_id),
        ]
    )
    # เกณฑ์สำหรับทุนเรียนดี
    db.session.add_all(
        [
            Criterion(name="ผลการเรียนสะสม (GPA)", max_score=70, scholarship_id=sch2.scholarship_id),
            Criterion(name="เรียงความเป้าหมายชีวิต", max_score=30, scholarship_id=sch2.scholarship_id),
        ]
    )
    # เกณฑ์สำหรับทุนกิจกรรม
    db.session.add_all(
        [
            Criterion(name="ผลงาน/เกียรติบัตร", max_score=60, scholarship_id=sch3.scholarship_id),
            Criterion(name="การมีส่วนร่วมในวิทยาลัย", max_score=40, scholarship_id=sch3.scholarship_id),
        ]
    )
    db.session.commit()

    # 3. สร้างรายชื่อผู้สมัคร 10 คน (Applications) กระจายตามทุน
    students = [
        # ทุนอาหารกลางวัน (4 คน)
        Application(
            student_id="68114540214",
            student_name="นาย ทรงเดช จำปาเทศ",
            faculty="คณะวิศวกรรมศาสตร์",
            gpa="3.94",
            application_date="2026-02-01",
            scholarship_id=sch1.scholarship_id,
            status="approved",
        ),
        Application(
            student_id="68114540101",
            student_name="นางสาว สวยใส ใจชื่น",
            faculty="คณะวิทยาศาสตร์",
            gpa="3.20",
            application_date="2026-02-02",
            scholarship_id=sch1.scholarship_id,
            status="pending",
        ),
        Application(
            student_id="68114540102",
            student_name="นาย มานะ อดทน",
            faculty="คณะบริหารศาสตร์",
            gpa="2.85",
            application_date="2026-02-03",
            scholarship_id=sch1.scholarship_id,
            status="reviewing",
        ),
        Application(
            student_id="68114540103",
            student_name="นางสาว ขยัน เรียนดี",
            faculty="คณะศิลปศาสตร์",
            gpa="3.15",
            application_date="2026-02-03",
            scholarship_id=sch1.scholarship_id,
            status="interview",
        ),
        # ทุนเรียนดี (4 คน)
        Application(
            student_id="68114540215",
            student_name="นาย ปกรณ์เกียรติ มั่นคง",
            faculty="คณะวิศวกรรมศาสตร์",
            gpa="3.98",
            application_date="2026-02-04",
            scholarship_id=sch2.scholarship_id,
            status="approved",
        ),
        Application(
            student_id="68114540104",
            student_name="นางสาว ปัญญา เลิศล้ำ",
            faculty="คณะวิทยาศาสตร์",
            gpa="4.00",
            application_date="2026-02-04",
            scholarship_id=sch2.scholarship_id,
            status="reviewing",
        ),
        Application(
            student_id="68114540105",
            student_name="นาย ฉลาด รอบรู้",
            faculty="คณะบริหารศาสตร์",
            gpa="3.85",
            application_date="2026-02-05",
            scholarship_id=sch2.scholarship_id,
            status="pending",
        ),
        Application(
            student_id="68114540106",
            student_name="นางสาว สมองไว ใจสู้",
            faculty="คณะศิลปศาสตร์",
            gpa="3.92",
            application_date="2026-02-05",
            scholarship_id=sch2.scholarship_id,
            status="interview",
        ),
        # ทุนกิจกรรม (2 คน)
        Application(
            student_id="68114540107",
            student_name="นาย กล้าหาญ ชาญชัย",
            faculty="คณะนิติศาสตร์",
            gpa="2.50",
            application_date="2026-02-06",
            scholarship_id=sch3.scholarship_id,
            status="pending",
        ),
        Application(
            student_id="68114540108",
            student_name="นางสาว ร่าเริง แจ่มใส",
            faculty="คณะศิลปศาสตร์",
            gpa="3.45",
            application_date="2026-02-06",
            scholarship_id=sch3.scholarship_id,
            status="reviewing",
        ),
    ]

    db.session.add_all(students)
    db.session.commit()
    print("--- ฐานข้อมูลถูกรีเซ็ตและเพิ่มข้อมูลชุดใหญ่ 10 คน เรียบร้อยแล้ว ---")


@app.route("/")
def home():
    return redirect(url_for('login'))


@app.route("/login")
def login():
    """หน้าเข้าสู่ระบบ - เลือกระบบเจ้าหน้าที่ กรรมการ หรือนักศึกษา"""
    return render_template('login.html')


@app.route("/logout")
def logout():
    """ออกจากระบบไปยังหน้า login"""
    return redirect(url_for('login'))


if __name__ == "__main__":
    # รันแอปพลิเคชัน
    app.run(debug=True, host="0.0.0.0", port=5000)
