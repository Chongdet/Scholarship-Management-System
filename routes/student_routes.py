from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Student, Scholarship # อย่าลืม Import ข้อมูลที่ต้องใช้
import json

student_bp = Blueprint('student', __name__)


# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ
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
# ผู้รับผิดชอบ: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
# ==========================================

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_student_id = request.form.get('student_id') 
        input_password = request.form.get('password')

        student = Student.query.filter_by(student_id=input_student_id).first()

        if student and student.check_password(input_password):
            
            session.clear()
            session['user_id'] = student.student_id
            session['role'] = 'student'
            
            flash(f"เข้าสู่ระบบสำเร็จ! (อัปเดตข้อมูลจาก REG เรียบร้อยแล้ว)", "success")
            return redirect(url_for('student.dashboard'))
        else:
            flash("รหัสนักศึกษา หรือ รหัสผ่านไม่ถูกต้อง", "error")
            return render_template('login.html')
            
    return render_template('login.html')

@student_bp.route('/auto-match')
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ (Scholarship Auto-Matching)"""
    return render_template("student/auto_match.html")

# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

# ==========================================
# ฟีเจอร์: Profile Management (จัดการข้อมูลส่วนตัว)
# ==========================================
@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("student.login"))

    current_student_id = session["user_id"]
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    if not student_record:
        flash("ไม่พบข้อมูลประวัตินักศึกษาในระบบฐานข้อมูล", "error")
        return redirect(url_for("student.login"))

    if request.method == "POST":
        # 1. อัปเดตข้อมูลการติดต่อ
        student_record.mobile = request.form.get("mobile", student_record.mobile)
        student_record.facebook = request.form.get("facebook", student_record.facebook)
        student_record.line_id = request.form.get("line_id", student_record.line_id)
        student_record.address_current = request.form.get("address_current", student_record.address_current)

        # 2. ข้อมูลสถานะการกู้ยืมและสถานภาพสมรส
        student_record.loan_student_fund = True if request.form.get("loan_student_fund") == "TRUE" else False
        student_record.loan_type = request.form.get("loan_type", "")
        student_record.parents_status = request.form.get("parents_status", student_record.parents_status)
        
        # 3. ข้อมูลบิดา
        student_record.father_job = request.form.get("father_job", "")
        student_record.father_income = request.form.get("father_income", type=float, default=0.0)
        student_record.inc_father = request.form.get("inc_father", type=float, default=0.0)
        student_record.father_health = request.form.get("father_health", "")

        # 4. ข้อมูลมารดา
        student_record.mother_job = request.form.get("mother_job", "")
        student_record.mother_income = request.form.get("mother_income", type=float, default=0.0)
        student_record.inc_mother = request.form.get("inc_mother", type=float, default=0.0)
        student_record.mother_health = request.form.get("mother_health", "")

        # 5. ข้อมูลที่อยู่อาศัย
        student_record.housing_status = request.form.get("housing_status", "")
        student_record.rent_amount = request.form.get("rent_amount", type=float, default=0.0)
        student_record.housing_other = request.form.get("housing_other", "")

        # 6. ข้อมูลที่ดินเกษตร
        student_record.land_status = request.form.get("land_status", "")
        student_record.agri_own_amount = request.form.get("agri_own_amount", type=float, default=0.0)
        student_record.agri_rent_amount = request.form.get("agri_rent_amount", type=float, default=0.0)
        student_record.agri_rent_cost = request.form.get("agri_rent_cost", type=float, default=0.0)
        student_record.agri_other_detail = request.form.get("agri_other_detail", "")

        # 7. ข้อมูลผู้อุปการะ
        student_record.guardian_name = request.form.get("guardian_name", "")
        student_record.guardian_relation = request.form.get("guardian_relation", "")
        student_record.guardian_job = request.form.get("guardian_job", "")
        student_record.guardian_income = request.form.get("guardian_income", type=float, default=0.0)

        # 8. จัดการข้อมูล JSON (พี่น้อง)
        try:
            siblings_data = request.form.get("siblings_json")
            if siblings_data:
                student_record.siblings_list = json.loads(siblings_data)
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
    # 1. ตรวจสอบการ Login ก่อน
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อนสมัครทุน", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        # ส่วนนี้ไว้เขียน Logic บันทึกลง Database ต่อไป
        return "สมัครทุนสำเร็จ (Logic ในการสร้าง Application Record)"
    
    # 2. ดึงข้อมูลทุนทั้งหมดเพื่อไปแสดงใน Dropdown
    scholarships = Scholarship.query.all()

    # 3. ดึงข้อมูลนักศึกษาที่ Login อยู่มาเตรียมไว้สำหรับ Auto-fill
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    # 4. สร้างตัวแปร prefill โดยดึงค่าจากฐานข้อมูลมาใส่
    # ถ้าใน DB ไม่มีข้อมูล ให้ใส่เป็นค่าว่าง '' เพื่อไม่ให้หน้าเว็บ Error
    prefill_data = {
        'student_id': student.student_id if student else '',
        'first_name': student.name.split()[0] if student and student.name else '',
        'last_name': student.name.split()[1] if student and student.name and len(student.name.split()) > 1 else '',
        'faculty': student.faculty if student else '',
        # คุณสามารถเพิ่ม field อื่นๆ ที่ต้องการ Auto-fill ได้ที่นี่
    }

    return render_template("student/apply.html", 
                           scholarships=scholarships, 
                           prefill=prefill_data)

@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (InputDocument Upload)"""
    return "Student: Document Upload endpoint"

# ==========================================
# ฟีเจอร์: ออกจากระบบ (Logout)
# ==========================================
@student_bp.route('/logout')
def logout():
    # 1. ล้างข้อมูลใน Session ทั้งหมดเพื่อออกจากระบบ
    session.clear()
    
    # 2. แจ้งเตือนผู้ใช้ (ถ้าต้องการ)
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    
    # 3. บังคับเปลี่ยนหน้าไปที่หน้าแรกสุด http://127.0.0.1:5000/
    return redirect('/')