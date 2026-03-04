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
    db.create_all()

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

    # สร้างบัญชี Admin (Officer) พื้นฐาน
    if not Officer.query.filter_by(username="admin").first():
        admin = Officer(username="admin", name="ผู้ดูแลระบบหลัก (Officer)")
        admin.set_password("ubu123456") 
        db.session.add(admin)
        
    # 🌟 เพิ่มบัญชี กรรมการ (Director) สำหรับทดสอบระบบ
    if not Director.query.filter_by(username="director").first():
        director_test = Director(username="director", name="กรรมการพิจารณาทุน")
        director_test.set_password("ubu123456")
        db.session.add(director_test)
        
    db.session.commit()

    # สร้างข้อมูลตัวอย่าง Audit Log (ถ้ายังไม่มี) - โครงสร้างตามแบบบันทึกประวัติ
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


# 5. Route สำหรับหน้า Login หลัก (แยกตารางค้นหาตาม Role)
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