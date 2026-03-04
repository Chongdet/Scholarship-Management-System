from flask import Flask, redirect, url_for, render_template, request, session, flash
from sqlalchemy import inspect, text
# นำเข้า Blueprint (ตรวจสอบให้แน่ใจว่า path ไฟล์ถูกต้อง)
# หากคุณรวมไว้ในไฟล์เดียวกัน ให้เปลี่ยนเป็น from officer_routes import officer_bp, director_bp
from routes.director_routes import director_bp
from routes.officer_routes import officer_bp
from routes.student_routes import student_bp

# 1. นำเข้า db และ Models
from models import db, Scholarship, Criterion, Application, Student, Officer, Director, AuditLog
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "ubu-scholarship-secret-key"

# 2. ตั้งค่า Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "scholarship.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # จำกัดขนาด request สูงสุด 10 MB

db.init_app(app)

# ฟังก์ชันแปลงวันที่เป็นรูปแบบไทย (พุทธศักราช)
THAI_MONTHS = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
               'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']

def thai_date_format(dt):
    """แปลง datetime เป็น '21 มกราคม 2569 เวลา 01:16'"""
    if not dt:
        return '-'
    return f"{dt.day} {THAI_MONTHS[dt.month-1]} {dt.year + 543} เวลา {dt.strftime('%H:%M')}"

app.jinja_env.filters['thai_date'] = thai_date_format

# 3. ลงทะเบียน Blueprint
# เชื่อมต่อส่วนของ Officer และ Director เข้ากับ URL Prefix ที่กำหนด
app.register_blueprint(director_bp, url_prefix="/director")
app.register_blueprint(officer_bp, url_prefix="/officer")
app.register_blueprint(student_bp, url_prefix="/student")

# 4. การจัดการ Database และสร้างบัญชีทดสอบ
with app.app_context():
    # หมายเหตุ: เอา db.drop_all() ออก เพื่อไม่ให้ข้อมูลผู้ใช้หรือตารางหายเมื่อรันใหม่
    db.create_all()

    # --- ส่วนที่ 1: ตรวจสอบและอัปเดตโครงสร้างตาราง (จาก main) ---
    inspector = inspect(db.engine)
    existing_columns = {col["name"] for col in inspector.get_columns("application")}
    if "reviewing_by" not in existing_columns:
        db.session.execute(text("ALTER TABLE application ADD COLUMN reviewing_by VARCHAR(50)"))
        db.session.commit()
    if "reviewing_at" not in existing_columns:
        db.session.execute(text("ALTER TABLE application ADD COLUMN reviewing_at DATETIME"))
        db.session.commit()

    # เพิ่มคอลัมน์ scholarship.announcement_date ถ้ายังไม่มี
    if "scholarship" in inspector.get_table_names():
        sch_cols = {col["name"] for col in inspector.get_columns("scholarship")}
        if "announcement_date" not in sch_cols:
            db.session.execute(text("ALTER TABLE scholarship ADD COLUMN announcement_date DATETIME"))
            db.session.commit()

    # เพิ่มคอลัมน์ audit_log ถ้ามีตารางอยู่แล้ว (เพื่อรองรับ schema เก่า)
    try:
        if "audit_log" in inspector.get_table_names():
            audit_cols = {col["name"] for col in inspector.get_columns("audit_log")}
            if "officer_label" not in audit_cols:
                db.session.execute(text("ALTER TABLE audit_log ADD COLUMN officer_label VARCHAR(50)"))
                db.session.commit()
            if "action_title" not in audit_cols:
                db.session.execute(text("ALTER TABLE audit_log ADD COLUMN action_title VARCHAR(100)"))
                db.session.commit()
            if "reference_id" not in audit_cols:
                db.session.execute(text("ALTER TABLE audit_log ADD COLUMN reference_id VARCHAR(30)"))
                db.session.commit()
            if "status_after" not in audit_cols:
                db.session.execute(text("ALTER TABLE audit_log ADD COLUMN status_after VARCHAR(100)"))
                db.session.commit()
            if "previous_value" not in audit_cols:
                db.session.execute(text("ALTER TABLE audit_log ADD COLUMN previous_value VARCHAR(200)"))
                db.session.commit()
    except Exception:
        pass

    # --- ส่วนที่ 2: สร้างบัญชีพื้นฐาน (จาก main) ---
    if not Officer.query.filter_by(username="admin").first():
        admin = Officer(username="admin", name="ผู้ดูแลระบบหลัก (Officer)")
        admin.set_password("ubu123456") 
        db.session.add(admin)
        
    if not Director.query.filter_by(username="director").first():
        director_test = Director(username="director", name="กรรมการพิจารณาทุน")
        director_test.set_password("ubu123456")
        db.session.add(director_test)
        
    db.session.commit()

    # --- ส่วนที่ 3: สร้างข้อมูลจำลอง ทุนการศึกษาและนักศึกษา (จากฝั่ง Yotsaran) ---
    # เช็คก่อนว่ามีข้อมูลในระบบหรือยัง ถ้ายังไม่มีถึงจำลองข้อมูล เพื่อป้องกัน error ข้อมูลซ้ำ
    if Scholarship.query.count() == 0:
        # 1. สร้างรายชื่อทุน (Scholarships)
        sch1 = Scholarship(scholarship_id="SCH-001", scholarship_name="ทุนอาหารกลางวัน")
        sch2 = Scholarship(scholarship_id="SCH-002", scholarship_name="ทุนเรียนดี (GPA สูง)")
        sch3 = Scholarship(scholarship_id="SCH-003", scholarship_name="ทุนกิจกรรมเด่น")
        db.session.add_all([sch1, sch2, sch3])
        db.session.commit()

        # 2. สร้างเกณฑ์คะแนนแยกตามทุน (Criteria)
        db.session.add_all([
            Criterion(name="สถานะความขาดแคลน", max_score=50, scholarship_id=sch1.scholarship_id),
            Criterion(name="ความประพฤติ", max_score=30, scholarship_id=sch1.scholarship_id),
            Criterion(name="สัมภาษณ์", max_score=20, scholarship_id=sch1.scholarship_id),
        ])
        db.session.add_all([
            Criterion(name="ผลการเรียนสะสม (GPA)", max_score=70, scholarship_id=sch2.scholarship_id),
            Criterion(name="เรียงความเป้าหมายชีวิต", max_score=30, scholarship_id=sch2.scholarship_id),
        ])
        db.session.add_all([
            Criterion(name="ผลงาน/เกียรติบัตร", max_score=60, scholarship_id=sch3.scholarship_id),
            Criterion(name="การมีส่วนร่วมในวิทยาลัย", max_score=40, scholarship_id=sch3.scholarship_id),
        ])
        db.session.commit()

        # 3. สร้างรายชื่อผู้สมัคร 10 คน (Applications) กระจายตามทุน
        students = [
            # ทุนอาหารกลางวัน (4 คน)
            Application(student_id="68114540214", student_name="นาย ทรงเดช จำปาเทศ", faculty="คณะวิศวกรรมศาสตร์", gpa="3.94", application_date="2026-02-01", scholarship_id=sch1.scholarship_id, status="approved"),
            Application(student_id="68114540101", student_name="นางสาว สวยใส ใจชื่น", faculty="คณะวิทยาศาสตร์", gpa="3.20", application_date="2026-02-02", scholarship_id=sch1.scholarship_id, status="pending"),
            Application(student_id="68114540102", student_name="นาย มานะ อดทน", faculty="คณะบริหารศาสตร์", gpa="2.85", application_date="2026-02-03", scholarship_id=sch1.scholarship_id, status="reviewing"),
            Application(student_id="68114540103", student_name="นางสาว ขยัน เรียนดี", faculty="คณะศิลปศาสตร์", gpa="3.15", application_date="2026-02-03", scholarship_id=sch1.scholarship_id, status="interview"),
            # ทุนเรียนดี (4 คน)
            Application(student_id="68114540215", student_name="นาย ปกรณ์เกียรติ มั่นคง", faculty="คณะวิศวกรรมศาสตร์", gpa="3.98", application_date="2026-02-04", scholarship_id=sch2.scholarship_id, status="approved"),
            Application(student_id="68114540104", student_name="นางสาว ปัญญา เลิศล้ำ", faculty="คณะวิทยาศาสตร์", gpa="4.00", application_date="2026-02-04", scholarship_id=sch2.scholarship_id, status="reviewing"),
            Application(student_id="68114540105", student_name="นาย ฉลาด รอบรู้", faculty="คณะบริหารศาสตร์", gpa="3.85", application_date="2026-02-05", scholarship_id=sch2.scholarship_id, status="pending"),
            Application(student_id="68114540106", student_name="นางสาว สมองไว ใจสู้", faculty="คณะศิลปศาสตร์", gpa="3.92", application_date="2026-02-05", scholarship_id=sch2.scholarship_id, status="interview"),
            # ทุนกิจกรรม (2 คน)
            Application(student_id="68114540107", student_name="นาย กล้าหาญ ชาญชัย", faculty="คณะนิติศาสตร์", gpa="2.50", application_date="2026-02-06", scholarship_id=sch3.scholarship_id, status="pending"),
            Application(student_id="68114540108", student_name="นางสาว ร่าเริง แจ่มใส", faculty="คณะศิลปศาสตร์", gpa="3.45", application_date="2026-02-06", scholarship_id=sch3.scholarship_id, status="reviewing"),
        ]
        db.session.add_all(students)
        db.session.commit()
        print("--- ฐานข้อมูลถูกสร้างและเพิ่มข้อมูลชุดใหญ่ 10 คน เรียบร้อยแล้ว ---")

    # --- ส่วนที่ 4: สร้างข้อมูลตัวอย่าง Audit Log (จาก main) ---
    try:
        if AuditLog.query.count() == 0:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            samples = [
                AuditLog(officer_username="admin", officer_label="เจ้าหน้าที่(A)", action="approved_interview", action_title="อนุมัติและนัดสัมภาษณ์", reference_id="APP345", details="อนุมัติใบสมัครทุนการศึกษาของ นภัสสร สวยงาม", status_after="เรียกสัมภาษณ์", previous_value="รอการตรวจสอบ", created_at=now - timedelta(hours=1)),
                AuditLog(officer_username="admin2", officer_label="เจ้าหน้าที่(B)", action="rejected", action_title="ปฏิเสธ", reference_id="APP346", details="ปฏิเสธใบสมัครทุนการศึกษาของ นภัสสร สวยงาม เหตุผล: เอกสารไม่ครบ", status_after="ปฏิเสธ", previous_value="รอการตรวจสอบ", created_at=now - timedelta(hours=2)),
                AuditLog(officer_username="admin3", officer_label="เจ้าหน้าที่(D)", action="create_scholarship", action_title="สร้างทุน", reference_id="SCH001", details='ได้ทำการสร้างทุน ทุนการศึกษา "บริษัท ไฮโวลเตจ เทคโนโลยี จำกัด" จำนวน 1 ทุน ๆ ละ 20,000 บาท', status_after="สร้างทุนแล้ว", created_at=now - timedelta(hours=3)),
                AuditLog(officer_username="admin4", officer_label="เจ้าหน้าที่(E)", action="announce_scholarship", action_title="ประกาศทุน", reference_id="SCH001", details='ได้ทำการประกาศทุน ทุนการศึกษา "บริษัท ไฮโวลเตจ เทคโนโลยี จำกัด" จำนวน 1 ทุน ๆ ละ 20,000 บาท', status_after="ประกาศผลแล้ว", created_at=now - timedelta(hours=4)),
            ]
            for s in samples:
                db.session.add(s)
            db.session.commit()
    except Exception:
        pass

    print("--- System Ready: Created accounts 'admin' and 'director' ---")


# 5. Route สำหรับหน้า Login หลัก
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role_target = request.form.get("role") # 'officer' หรือ 'director'

        if not username or not password:
            flash("กรุณากรอกทั้งชื่อผู้ใช้งานและรหัสผ่าน", "error")
            return render_template("login.html")

        # --- กรณี Login นักศึกษา ---
        if not role_target:
            student = Student.query.filter_by(student_id=username).first()
            if student and student.check_password(password):
                session.clear()
                session["user_id"] = student.student_id
                session["role"] = "student"
                return redirect(url_for("student.dashboard"))

        # --- กรณี Login เจ้าหน้าที่/กรรมการ ---
        else:
            user = None
            if role_target == "officer":
                user = Officer.query.filter_by(username=username).first()
            elif role_target == "director":
                user = Director.query.filter_by(username=username).first()

            if user and user.check_password(password):
                session.clear()
                session["user_id"] = user.username
                session["role"] = role_target
                flash(f"ยินดีต้อนรับคุณ {user.name}", "success")
                
                # แยกทางไปตาม Role
                if role_target == "officer":
                    return redirect(url_for("officer.list_scholarships"))
                elif role_target == "director":
                    # ชี้ไปยังหน้าแรกของกรรมการ (ที่ชื่อฟังก์ชัน home ใน director_bp)
                    return redirect(url_for("director.home"))
            
        flash("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง", "error")

    return render_template("login.html")

@app.route("/")
def index():
    all_scholarships = Scholarship.query.all()
    return render_template("index.html", scholarships=all_scholarships)

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)