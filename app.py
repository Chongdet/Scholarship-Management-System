from flask import Flask, redirect, url_for, render_template, request, session, flash
from sqlalchemy import inspect, text
import os

# นำเข้า Blueprint (ตรวจสอบให้แน่ใจว่า path ไฟล์ถูกต้อง)
from routes.director_routes import director_bp
from routes.officer_routes import officer_bp
from routes.student_routes import student_bp

# 1. นำเข้า db และ Models
from models import db, Scholarship, Criterion, Application, Student, Officer, Director

app = Flask(__name__)
app.config["SECRET_KEY"] = "ubu-scholarship-secret-key"

# --- 🚀 ส่วนที่แก้ไข: ตั้งค่า UPLOAD_FOLDER และสร้างโฟลเดอร์อัตโนมัติ ---
basedir = os.path.abspath(os.path.dirname(__file__)) # หา Path ปัจจุบันของโปรเจกต์
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# เช็คว่ามีโฟลเดอร์ static/uploads หรือยัง ถ้ายังไม่มีให้สร้างขึ้นมาเลย
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"--- 📁 Created Upload Folder at: {UPLOAD_FOLDER} ---")
# -----------------------------------------------------------------

# 2. ตั้งค่า Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "scholarship.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # จำกัดขนาด request สูงสุด 10 MB

db.init_app(app)

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
    print("--- 🚀 System Ready: สร้างบัญชี 'admin' และ 'director' สำเร็จ ---")


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