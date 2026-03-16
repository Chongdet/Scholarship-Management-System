import os
import json
import uuid
from flask import Blueprint, current_app, render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from models import db, Student, Scholarship, Application
from services.reg_service import RegService
from services.matching_service import MatchingService

student_bp = Blueprint('student', __name__)

@student_bp.before_request
def require_student_login():
    """ตรวจสอบการล็อกอินก่อนเข้าถึงทุก Route ของ Student (ยกเว้นหน้า login)"""
    if request.endpoint and request.endpoint != 'student.login':
        if "user_id" not in session or session.get("role") != "student":
            flash("กรุณาเข้าสู่ระบบในฐานะนักศึกษา", "error")
            return redirect(url_for("student.login"))

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# Dashboard & Landing
# ==========================================
# รับผิดชอบโดย: นางสาว ปัญญาพร มูลดับ
@student_bp.route("/dashboard")
def dashboard():
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("student.login"))

    all_scholarships = Scholarship.query.all()
    return render_template("student/dashboard.html", student=student, scholarships=all_scholarships)

# ==========================================
# Login / Logout
# ==========================================
# รับผิดชอบโดย: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_student_id = request.form.get('student_id')
        input_password   = request.form.get('password')

        is_valid, reg_data_or_msg = RegService.validate_credentials(input_student_id, input_password)

        if is_valid:
            reg_data = RegService.fetch_profile(input_student_id)
            student = Student.query.filter_by(student_id=input_student_id).first()
            
            if not student:
                student = Student(student_id=input_student_id)
                db.session.add(student)

            # Sync ข้อมูลจาก REG Service
            student.gpax = reg_data.get('gpax')
            student.faculty = reg_data.get('faculty')
            student.year = reg_data.get('year')
            student.disciplinary_status = reg_data.get('disciplinary_status')
            student.set_password(input_password)

            db.session.commit()

            session.clear()
            session['user_id'] = student.student_id
            session['role'] = 'student'

            flash("เข้าสู่ระบบสำเร็จ! อัปเดตข้อมูลจาก REG เรียบร้อย", "success")
            return redirect(url_for('student.dashboard'))
        else:
            flash(f"การเข้าสู่ระบบล้มเหลว: {reg_data_or_msg}", "error")
    
    return render_template('login.html')

@student_bp.route('/logout')
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect(url_for("student.login"))

# ==========================================
# ฟีเจอร์: Profile Management
# ==========================================
# รับผิดชอบโดย: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
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
        student_record.inc_guardian    = safe_float("inc_guardian")
        student_record.inc_scholarship = safe_float("inc_scholarship")
        student_record.inc_parttime    = safe_float("inc_parttime")

        student_record.exp_food      = safe_float("exp_food")
        student_record.exp_dorm      = safe_float("exp_dorm")
        student_record.exp_transport = safe_float("exp_transport")
        student_record.exp_other     = safe_float("exp_other")
        db.session.commit()
        flash("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว ✅", "success")
        return redirect(url_for("student.profile"))
 
    return render_template("student/profile.html", student=student_record)

# ==========================================
# Scholarship Matching & Application
# ==========================================
# รับผิดชอบโดย: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
@student_bp.route('/auto-match')
def auto_match():
    student = Student.query.filter_by(student_id=session["user_id"]).first()
    matches = MatchingService.get_all_matches(student)
    return render_template("student/auto_match.html", student=student, matches=matches)

@student_bp.route("/scholarships/<scholarship_id>")
def scholarship_detail(scholarship_id):
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    student = Student.query.filter_by(student_id=session["user_id"]).first()
    
    existing_app = Application.query.filter_by(
        student_id=session["user_id"],
        scholarship_id=scholarship_id
    ).first()

    return render_template("student/scholarship_detail.html", 
                           scholarship=scholarship, 
                           student=student, 
                           already_applied=existing_app is not None)

# รับผิดชอบโดย: นาย จารุวัฒน์ บุญสาร
@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if request.method == "POST":
        scholarship_id = request.form.get("scholarship_id")
        action         = request.form.get("action", "submit")
        
        if not scholarship_id:
            flash("กรุณาเลือกทุนการศึกษา", "error")
            return redirect(url_for("student.apply_scholarship"))

        # ป้องกันการสมัครซ้ำ
        existing_app = Application.query.filter_by(
            student_id=current_student_id,
            scholarship_id=scholarship_id
        ).first()
        
        if existing_app:
            flash("คุณได้สมัครทุนนี้ไปแล้ว", "error")
            return redirect(url_for("student.dashboard"))

        # ข้อมูลนักศึกษาจากฟอร์ม
        first_name   = request.form.get("first_name", "")
        last_name    = request.form.get("last_name", "")
        student_name = f"{first_name} {last_name}".strip()
        faculty      = request.form.get("faculty", "")
        email        = request.form.get("email", "").strip()
        phone        = request.form.get("phone", "").strip()
        gpa_val      = request.form.get("gpa")
        address      = request.form.get("address", "")
        reason       = request.form.get("reason", "").strip()

        # อัปเดตข้อมูล Student จากฟอร์ม (เพื่อให้เจ้าหน้าที่เห็นข้อมูลถูกต้อง)
        if student:
            if student_name:
                student.name = student_name
            if faculty:
                student.faculty = faculty
            if email:
                student.email = email
            if phone:
                student.mobile = phone
            if address:
                student.address_current = address
            if gpa_val:
                try:
                    student.gpax = float(gpa_val)
                except (ValueError, TypeError):
                    pass
            db.session.commit()

        status = "draft" if action == "save_draft" else "pending"

        # รวบรวมข้อมูลทั้งหมดจากฟอร์มเพื่อเก็บเป็น JSON
        form_data_dict = {k: (v.strip() if isinstance(v, str) else v) for k, v in request.form.items()
                          if k not in ('scholarship_id', 'action', 'upload_student_id') and v}
        form_data_json = json.dumps(form_data_dict, ensure_ascii=False) if form_data_dict else None
        
        new_app = Application(
            id=f"APP-{current_student_id}-{scholarship_id}-{uuid.uuid4().hex[:4]}",
            student_id=current_student_id,
            student_name=student_name if student_name else (student.name if student else ""),
            faculty=faculty if faculty else (student.faculty if student else ""),
            scholarship_id=scholarship_id,
            status=status,
            notes=reason if reason else None,
            form_data=form_data_json
        )
        db.session.add(new_app)
        
        # --- จัดการไฟล์แนบ ---
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_student_id))
        os.makedirs(upload_folder, exist_ok=True)

        # รับไฟล์ได้ทั้งจากชื่อ field 'documents' และ 'document'
        files = request.files.getlist("documents")
        if not files or all(f.filename == '' for f in files):
            single_file = request.files.get("document")
            if single_file and single_file.filename != '':
                files = [single_file]

        first_filename = None
        for file in files:
            if file and allowed_file(file.filename):
                filename        = secure_filename(file.filename)
                unique_filename = f"app_{new_app.id}_{uuid.uuid4().hex[:8]}_{filename}"

                if not first_filename:
                    first_filename = unique_filename

                save_path = os.path.join(upload_folder, unique_filename)
                file.save(save_path)

        if first_filename:
            new_app.application_file = first_filename

        db.session.commit()
        flash("ส่งใบสมัครเรียบร้อยแล้ว", "success")
        return redirect(url_for("student.track_status"))

    # --- ฝั่ง GET Method ---
    scholarships = Scholarship.query.all()
    
    prefill = {}
    req_sch_id = request.args.get("scholarship_id")
    if req_sch_id:
        prefill["scholarship_id"] = req_sch_id
        
    if student:
        parts      = student.name.split() if student.name else [""]
        first_name = parts[0]
        last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""
        prefill.update({
            "student_id": student.student_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": student.email or "",
            "phone": student.mobile or "",
            "faculty": student.faculty or "",
            "gpa": student.gpax if student.gpax is not None else "",
            "address": student.address_current or "",
        })

    titles          = ["นาย", "นางสาว", "นาง"]
    genders         = ["ชาย", "หญิง"]
    housing_types   = ["บ้านพัก", "ที่อยู่อาศัย", "ที่พัก"]
    parent_statuses = ["มีชีวิตอยู่", "ถึงแก่กรรม", "หย่าร้าง", "แยกกันอยู่"]
    year_levels     = [1, 2, 3, 4, 5, 6]
    faculties       = [
        "คณะเกษตรศาสตร์", "คณะวิทยาศาสตร์", "คณะวิศวกรรมศาสตร์", "คณะศิลปศาสตร์",
        "คณะเภสัชศาสตร์", "คณะบริหารศาสตร์", "คณะพยาบาลศาสตร์",
        "วิทยาลัยแพทยศาสตร์และการสาธารณสุข", "คณะศิลปประยุกต์และสถาปัตยกรรมศาสตร์",
        "คณะนิติศาสตร์", "คณะรัฐศาสตร์"
    ]

    return render_template("student/apply.html",
                           scholarships=scholarships,
                           prefill=prefill,
                           titles=titles,
                           genders=genders,
                           faculties=faculties,
                           year_levels=year_levels,
                           parent_statuses=parent_statuses,
                           housing_types=housing_types)

# รับผิดชอบโดย: นาย จารุวัฒน์ บุญสาร
@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (เผื่อใช้รับไฟล์ผ่าน AJAX แยกต่างหาก)"""
    return "Student: Document Upload endpoint"

@student_bp.route("/scholarships")
def announce_scholarships():
    all_scholarships = Scholarship.query.all()
    return render_template("student/scholarships.html", scholarships=all_scholarships)


# รับผิดชอบโดย: นางสาว ปัญญาพร มูลดับ
@student_bp.route("/status")
def track_status():
    student_id = session.get("user_id")

    page = request.args.get('page', 1, type=int)
    pagination = Application.query.filter_by(student_id=student_id)\
        .order_by(Application.created_at.desc())\
        .paginate(page=page, per_page=5, error_out=False)

    for app in pagination.items:
        user_upload_dir = os.path.join(current_app.static_folder, 'uploads', str(student_id))
        app.all_files = []
        if os.path.exists(user_upload_dir):
            all_entries = os.listdir(user_upload_dir)
            app.all_files = [f for f in all_entries if f.startswith(f"app_{app.id}")]

    return render_template("student/status.html", pagination=pagination)


@student_bp.route("/status/detail/<app_id>")
def status_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("student/status_detail.html", app=application)