from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models import db, Scholarship, Application, Student
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

student_bp = Blueprint("student", __name__)

# ==========================================
# ฟีเจอร์: Dashboard
# ==========================================
@student_bp.route("/dashboard")
def dashboard():
    # ตรวจสอบการ Login
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("login"))

    # ดึงข้อมูลนักศึกษาที่ Login จากฐานข้อมูลจริง
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("login"))

    # ดึงข้อมูลทุนทั้งหมดมาแสดง
    all_scholarships = Scholarship.query.all()

    return render_template("student/dashboard.html", 
                           student=student, 
                           scholarships=all_scholarships)

# ==========================================
# ฟีเจอร์: Profile Management (จัดการข้อมูลส่วนตัว)
# ==========================================
@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))

    current_student_id = session["user_id"]
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    if not student_record:
        flash("ไม่พบข้อมูลประวัตินักศึกษา", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        # 1. อัปเดตข้อมูลการติดต่อ
        student_record.mobile = request.form.get("mobile", student_record.mobile)
        student_record.facebook = request.form.get("facebook", student_record.facebook)
        student_record.line_id = request.form.get("line_id", student_record.line_id)
        student_record.address_current = request.form.get("address_current", student_record.address_current)

        # 2. ข้อมูลสถานะการกู้ยืมและครอบครัว
        student_record.loan_student_fund = True if request.form.get("loan_student_fund") == "TRUE" else False
        student_record.loan_type = request.form.get("loan_type", "")
        student_record.parents_status = request.form.get("parents_status", student_record.parents_status)
        
        # 3. ข้อมูลรายได้ (รองรับทศนิยม)
        student_record.inc_father = request.form.get("inc_father", type=float, default=0.0)
        student_record.inc_mother = request.form.get("inc_mother", type=float, default=0.0)
        student_record.inc_guardian = request.form.get("inc_guardian", type=float, default=0.0)

        # 4. จัดการข้อมูล JSON (พี่น้อง และ ประวัติทุน)
        try:
            siblings_data = request.form.get("siblings_json")
            if siblings_data:
                student_record.siblings_list = json.loads(siblings_data)
            
            scholarships_data = request.form.get("scholarships_json")
            if scholarships_data:
                student_record.scholarship_history = json.loads(scholarships_data)
        except Exception as e:
            print(f"JSON Error: {e}")

        db.session.commit()
        flash("อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student_record)

# ==========================================
# ฟีเจอร์: การสมัครทุนและจัดการไฟล์
# ==========================================
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    if request.method == "POST":
        # โครงสร้างการสมัครทุน (Logic จากคุณจารุวัฒน์)
        return "สมัครทุนสำเร็จ (Logic ในการสร้าง Application Record)"
    
    scholarships = Scholarship.query.all()
    return render_template("student/scholarships.html", scholarships=scholarships)

@student_bp.route("/status")
def track_status():
    """ระบบติดตามสถานะการสมัคร"""
    from datetime import datetime
    
    class MockApp:
        def __init__(self, id, name, type, faculty, status, date, files):
            self.id = id
            self.scholarship_name = name
            self.scholarship_type = type
            self.faculty = faculty
            self.status = status
            self.created_at = datetime.strptime(date, '%Y-%m-%d')
            self.open_date = datetime(2025, 10, 1)
            self.close_date = datetime(2025, 10, 31)
            self.files = files

    # รายการไฟล์จำลอง 5 ไฟล์ที่นักศึกษามักต้องส่ง
    my_files = [
        {"name": "1_สำเนาบัตรประชาชน.pdf"},
        {"name": "2_ระเบียนผลการเรียน_GPAX.pdf"},
        {"name": "3_รูปถ่ายสภาพบ้านพักปัจจุบัน.pdf"},
        {"name": "4_สำเนาทะเบียนบ้าน.pdf"},
        {"name": "5_หนังสือรับรองรายได้ครอบครัว.pdf"}
    ]

    # จำลองข้อมูล 5 ทุน คละสถานะ
    applications = [
        MockApp(1, "ทุนบริษัท ไฮโวลเตจ เทคโนโลยี จำกัด", "ทุนบริจาค", "คณะวิศวกรรมศาสตร์", "รอตรวจสอบ", "2025-10-15", my_files),
        MockApp(2, "ทุนเรียนดีเพื่ออุดมศึกษา", "ทุนภายใน", "คณะวิทยาศาสตร์", "เรียกสัมภาษณ์", "2025-10-18", my_files),
        MockApp(3, "ทุนช่วยเหลือค่าครองชีพ กยศ.", "ทุนภายนอก", "ส่วนกลาง", "ปฏิเสธ", "2025-10-20", my_files),
        MockApp(4, "ทุนนักกิจกรรมตัวอย่าง", "ทุนภายใน", "คณะบริหารศาสตร์", "ได้รับทุน", "2025-10-22", my_files),
        MockApp(5, "ทุนเยียวยานักศึกษาจากภัยพิบัติ", "ทุนฉุกเฉิน", "ส่วนกลาง", "รอตรวจสอบ", "2025-10-25", my_files)
    ]
    
    return render_template("student/status.html", applications=applications)

@student_bp.route("/status_detail/<int:app_id>")
def status_detail(app_id):
    from datetime import datetime
    # ข้อมูลรายละเอียดสำหรับ 5 ID
    mock_db = {
        1: {"name": "ทุนบริษัท ไฮโวลเตจ เทคโนโลยี จำกัด", "status": "รอตรวจสอบ", "desc": "เจ้าหน้าที่กำลังตรวจสอบความถูกต้องของเอกสาร"},
        2: {"name": "ทุนเรียนดีเพื่ออุดมศึกษา", "status": "เรียกสัมภาษณ์", "desc": "วันที่ 5 ธ.ค. 68 เวลา 09:00 น. ณ ห้องประชุม EN101"},
        3: {"name": "ทุนช่วยเหลือค่าครองชีพ กยศ.", "status": "ปฏิเสธ", "desc": "เนื่องจากรายได้ครอบครัวเกินเกณฑ์ที่กำหนด"},
        4: {"name": "ทุนนักกิจกรรมตัวอย่าง", "status": "ได้รับทุน", "desc": "ยินดีด้วย! ท่านได้รับการคัดเลือก กรุณามารายงานตัว"},
        5: {"name": "ทุนเยียวยานักศึกษาจากภัยพิบัติ", "status": "รอตรวจสอบ", "desc": "อยู่ระหว่างพิจารณาความเร่งด่วน"}
    }
    
    info = mock_db.get(app_id, mock_db[1])

    class MockDetail:
        def __init__(self, id, data):
            self.id = id
            self.scholarship = type('Obj', (object,), {'name': data['name'], 'amount': 20000.0})
            self.faculty = "คณะวิศวกรรมศาสตร์"
            self.status = data['status']
            self.status_description = data['desc']
            self.created_at = datetime(2025, 10, 15)
            self.reviewing_at = datetime(2025, 11, 20)

    app_data = MockDetail(app_id, info)
    return render_template("student/status_detail.html", app=app_data)


@student_bp.route("/auto-match")
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ"""
    return render_template("student/auto_match.html")