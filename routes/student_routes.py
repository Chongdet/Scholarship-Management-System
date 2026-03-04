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
            siblings_data = request.form.get("siblings_json")
            if siblings_data and siblings_data.strip():
                student_record.siblings_list = json.loads(siblings_data)
            
            scholarships_data = request.form.get("scholarships_json")
            if scholarships_data and scholarships_data.strip():
                student_record.scholarship_history = json.loads(scholarships_data)
        except Exception as e:
            print(f"JSON Error: {e}")

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
    housing_types = ["บ้านพัก", "ที่อยู่อาศัย", "ที่พัก"]
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("login"))

    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if request.method == "POST":
        # รับข้อมูลจากแบบฟอร์ม
        scholarship_id = request.form.get("scholarship_id")
        action = request.form.get("action", "submit")
        
        # ข้อมูลนักศึกษาจากฟอร์ม
        first_name = request.form.get("first_name", "")
        last_name = request.form.get("last_name", "")
        student_name = f"{first_name} {last_name}".strip()
        faculty = request.form.get("faculty", "")
        
        if not scholarship_id:
            flash("กรุณาเลือกทุนการศึกษา", "error")
            return redirect(url_for("student.apply_scholarship"))

        # ตรวจสอบว่าเคยสมัครทุนนี้หรือยัง
        existing_app = Application.query.filter_by(student_id=current_student_id, scholarship_id=scholarship_id).first()
        if existing_app:
            flash("คุณได้สมัครทุนนี้ไปแล้ว", "error")
            return redirect(url_for("student.dashboard"))
        
        # จัดการสถานะ (บันทึกร่าง หรือ ส่งใบสมัคร)
        status = "draft" if action == "save_draft" else "pending"
        
        # บันทึกข้อมูลลงฐานข้อมูล Application
        new_app = Application(
            student_id=current_student_id,
            student_name=student_name if student_name else student.name,
            faculty=faculty if faculty else student.faculty,
            scholarship_id=scholarship_id,
            status=status
        )
        db.session.add(new_app)
        db.session.commit()
        
        # --- จัดการไฟล์แนบ ---
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', current_student_id)
        os.makedirs(upload_folder, exist_ok=True)
            
        files = request.files.getlist("documents")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # ผูกไฟล์กับ Application ID เพื่อไม่ให้สับสน
                save_path = os.path.join(upload_folder, f"app_{new_app.id}_{filename}")
                file.save(save_path)
        
        flash("บันทึกข้อมูลการสมัครเรียบร้อยแล้ว", "success")
        return redirect(url_for("student.dashboard"))
    
    # GET method
    scholarships = Scholarship.query.all()
    
    # ดึงข้อมูลนักศึกษามาแสดงไว้ก่อน (Prefill)
    prefill = {}
    if student:
        parts = student.name.split() if student.name else [""]
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        prefill = {
            "student_id": student.student_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": student.email,
            "faculty": student.faculty
        }

    titles = ["นาย", "นางสาว", "นาง"]
    genders = ["ชาย", "หญิง"]
    faculties = [
        "คณะเกษตรศาสตร์", "คณะวิทยาศาสตร์", "คณะวิศวกรรมศาสตร์", "คณะศิลปศาสตร์", 
        "คณะเภสัชศาสตร์", "คณะบริหารศาสตร์", "คณะพยาบาลศาสตร์", 
        "วิทยาลัยแพทยศาสตร์และการสาธารณสุข", "คณะศิลปประยุกต์และสถาปัตยกรรมศาสตร์", 
        "คณะนิติศาสตร์", "คณะรัฐศาสตร์"
    ]
    year_levels = [1, 2, 3, 4, 5, 6]
    parent_statuses = ["มีชีวิตอยู่", "ถึงแก่กรรม", "หย่าร้าง", "แยกกันอยู่"]

    return render_template("student/apply.html", 
                           scholarships=scholarships, 
                           prefill=prefill,
                           titles=titles,
                           genders=genders,
                           faculties=faculties,
                           year_levels=year_levels,
                           parent_statuses=parent_statuses,
                           housing_types=housing_types)

@student_bp.route("/status")
def track_status():
    """ระบบติดตามสถานะการสมัคร"""
    
@student_bp.route("/auto-match")
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ"""
    return render_template("student/auto_match.html")
