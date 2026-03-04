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
        input_password   = request.form.get('password')

        is_valid, message = RegService.authenticate(input_student_id, input_password)

        if is_valid:
            reg_data = RegService.fetch_profile(input_student_id)

            student = Student.query.filter_by(student_id=input_student_id).first()
            if not student:
                student = Student(student_id=input_student_id)
                db.session.add(student)

            # [Sync Policy] REG Data overrides local
            student.gpax                = reg_data['gpax']
            student.faculty             = reg_data['faculty']
            student.year                = reg_data['year']
            student.disciplinary_status = reg_data['disciplinary_status']
            student.set_password(input_password)

            db.session.commit()

            session.clear()
            session['user_id'] = student.student_id
            session['role']    = 'student'

            flash(f"เข้าสู่ระบบสำเร็จ! อัปเดต GPAX: {student.gpax} จาก REG แล้ว", "success")
            return redirect(url_for('student.dashboard'))
        else:
            flash(f"การเข้าสู่ระบบล้มเหลว: {message}", "error")
            return render_template('login.html')

    return render_template('login.html')


# ==========================================
# ฟีเจอร์: Profile Management
# ==========================================
@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("student.login"))

    current_student_id = session["user_id"]
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    if not student_record:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("student.login"))

    if request.method == "POST":

        # ── Helper: แปลง float ปลอดภัย (รับ '' และ None ได้) ──────────
        def safe_float(key, default=None):
            val = request.form.get(key, '').strip()
            if val == '':
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        # ══════════════════════════════════════════════════════════════
        # [Security] ห้ามรับ gpax / faculty / year / citizen_id /
        #             address_domicile / disciplinary_status จาก form
        # ══════════════════════════════════════════════════════════════

        # ── 1. ประวัติส่วนตัว (editable) ─────────────────────────────
        student_record.mobile           = request.form.get("mobile",   "").strip() or None
        student_record.facebook         = request.form.get("facebook", "").strip() or None
        student_record.line_id          = request.form.get("line_id",  "").strip() or None
        student_record.address_current  = request.form.get("address_current", "").strip() or None

        # ── 2. บิดา ───────────────────────────────────────────────────
        student_record.father_name      = request.form.get("father_name",   "").strip() or None
        student_record.father_job       = request.form.get("father_job",    "").strip() or None
        student_record.father_income    = safe_float("father_income")
        student_record.inc_father       = safe_float("inc_father")
        student_record.father_health    = request.form.get("father_health", "").strip() or None

        # ── 3. มารดา ──────────────────────────────────────────────────
        student_record.mother_name      = request.form.get("mother_name",   "").strip() or None
        student_record.mother_job       = request.form.get("mother_job",    "").strip() or None
        student_record.mother_income    = safe_float("mother_income")
        student_record.inc_mother       = safe_float("inc_mother")
        student_record.mother_health    = request.form.get("mother_health", "").strip() or None

        # ── 4. สถานภาพสมรสบิดา-มารดา ─────────────────────────────────
        student_record.parents_status   = request.form.get("parents_status") or None

        # ── 5. ที่อยู่อาศัย ───────────────────────────────────────────
        student_record.housing_status   = request.form.get("housing_status") or None
        student_record.rent_amount      = safe_float("rent_amount")
        student_record.housing_other    = request.form.get("housing_other", "").strip() or None

        # ── 6. ที่ดินเกษตร ────────────────────────────────────────────
        student_record.land_status      = request.form.get("land_status") or None
        student_record.agri_own_amount  = safe_float("agri_own_amount")
        student_record.agri_rent_amount = safe_float("agri_rent_amount")
        student_record.agri_rent_cost   = safe_float("agri_rent_cost")
        student_record.agri_other_detail= request.form.get("agri_other_detail", "").strip() or None

        # ── 7. ผู้อุปการะ ─────────────────────────────────────────────
        student_record.guardian_name     = request.form.get("guardian_name",     "").strip() or None
        student_record.guardian_relation = request.form.get("guardian_relation", "").strip() or None
        student_record.guardian_job      = request.form.get("guardian_job",      "").strip() or None
        student_record.guardian_income   = safe_float("guardian_income")

        # ── 8. กยศ. ──────────────────────────────────────────────────
        loan_raw = request.form.get("loan_student_fund", "FALSE")
        student_record.loan_student_fund = (loan_raw == "TRUE")
        student_record.loan_type         = request.form.get("loan_type") or None

        # ── 9. พี่น้อง (รับ JSON จาก hidden field) ───────────────────
        # Template ส่งมาเป็น JSON string ใน hidden input ชื่อ siblings_json
        try:
            siblings_raw = request.form.get("siblings_json", "[]").strip()
            parsed = json.loads(siblings_raw)
            # Sanitize — เก็บเฉพาะ key ที่ต้องการ
            student_record.siblings_list = [
                {
                    "name":  str(s.get("name",  "") or "").strip(),
                    "age":   str(s.get("age",   "") or "").strip(),
                    "job":   str(s.get("job",   "") or "").strip(),
                    "place": str(s.get("place", "") or "").strip(),
                }
                for s in parsed if isinstance(s, dict)
            ]
        except (json.JSONDecodeError, TypeError):
            # ถ้า parse ไม่ได้ → คงค่าเดิม
            pass

        # ── 10. คำนวณ derived fields ──────────────────────────────────
        student_record.calculate_total_income()
        student_record.update_completeness()

        db.session.commit()
        flash("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว ✅", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student_record)

@student_bp.route('/auto-match')
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ (Scholarship Auto-Matching)"""
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("login"))
        
    from services.matching_service import MatchingService
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()
    
    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("login"))
        
    # ประมวลผลการจับคู่ทุนทั้งหมด
    matches = MatchingService.get_all_matches(student)
    
    return render_template("student/auto_match.html", 
                           student=student, 
                           matches=matches)

# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

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