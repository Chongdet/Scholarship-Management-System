from flask import Flask, redirect, url_for, render_template, request, session, flash
from sqlalchemy import inspect, text
# นำเข้า Blueprint (ตรวจสอบให้แน่ใจว่า path ไฟล์ถูกต้อง)
# หากคุณรวมไว้ในไฟล์เดียวกัน ให้เปลี่ยนเป็น from officer_routes import officer_bp, director_bp
from routes.director_routes import director_bp
from routes.officer_routes import officer_bp
from routes.student_routes import student_bp

# 1. นำเข้า db และ Models
from models import db, Scholarship, Criterion, Application, Student, Officer, Director
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

    # 🌟 เพิ่มบัญชี นักศึกษา (Student) สำหรับทดสอบระบบ
    if not Student.query.filter_by(student_id="6611111111").first():
        test_student = Student(
            student_id="6611111111", 
            name="นายสมชาย รักเรียน"
            # (ถ้าใน models.py ของคุณมีให้กรอก คณะ/สาขา เพิ่มเติม ก็ใส่ตรงนี้ได้เลย)
        )
        test_student.set_password("ubu123456")  # ตั้งรหัสผ่านเป็น ubu123456
        db.session.add(test_student)

    db.session.commit()
    print("--- 🚀 System Ready: สร้างบัญชี 'admin', 'director' และ 'student' สำเร็จ ---")

    # 🌟 เพิ่มข้อมูล ทุนการศึกษา (Scholarship) สำหรับทดสอบระบบ
    if not Scholarship.query.first():
        sc1 = Scholarship(name="ทุนเรียนดี ศรีอุบลฯ", amount=15000)
        sc2 = Scholarship(name="ทุนขาดแคลนทุนทรัพย์", amount=10000)
        sc3 = Scholarship(name="ทุนจิตอาสาพัฒนาสังคม", amount=8000)
        
        db.session.add_all([sc1, sc2, sc3])
        db.session.commit()
        print("--- 🚀 System Ready: สร้างข้อมูล 'ทุนการศึกษาจำลอง' สำเร็จ ---")


def mock_get_reg_data(student_id):
    """จำลองการดึงข้อมูลจากระบบทะเบียน (REG) ตามรหัสนักศึกษา"""
    reg_database = {
        "6611111111": {
            "name": "นายสมชาย รักเรียน",
            "faculty": "วิทยาศาสตร์",
            "gpax": 3.75,
            "address_current": "85 ถ.สถลมาร์ค ต.เมืองศรีไค อ.วารินชำราบ จ.อุบลราชธานี",
            "citizen_id": "1345678901234",
            "email": "somchai.r@ubu.ac.th",
            "address_domicile": "123 หมู่ 1 ต.ในเมือง อ.เมือง จ.อุบลราชธานี",
            "advisor_name": "ผศ.ดร.ใจดี เรียนเก่ง",
            "year": "ปี 2",
            "father_name": "นายสมบูรณ์ รักเรียน",
            "mother_name": "นางสมศรี รักเรียน",
            "disciplinary_status": "ไม่มี"
        }
    }
    return reg_database.get(student_id)
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
       # --- กรณี Login นักศึกษา ---
        if not role_target:
            student = Student.query.filter_by(student_id=username).first()
            if student and student.check_password(password):
                
                # --- [START] ดึงข้อมูลจาก REG จำลอง ---
                reg_data = mock_get_reg_data(student.student_id)
                if reg_data:
                    student.name = reg_data.get('name', student.name)
                    student.faculty = reg_data.get('faculty')
                    student.mobile = reg_data.get('mobile')
                    student.address_current = reg_data.get('address_current')
                    student.gpax = reg_data.get('gpax')
                    student.citizen_id = reg_data.get('citizen_id')
                    student.email = reg_data.get('email')
                    student.address_domicile = reg_data.get('address_domicile')
                    student.advisor_name = reg_data.get('advisor_name')
                    student.year = reg_data.get('year')
                    student.father_name = reg_data.get('father_name')
                    student.mother_name = reg_data.get('mother_name')
                    
                    db.session.commit() # เซฟลงฐานข้อมูล
                # --- [END] ---

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