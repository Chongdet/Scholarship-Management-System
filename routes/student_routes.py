import os
import json
import uuid
from flask import Blueprint, current_app, render_template, request, session, redirect, url_for, flash
from sqlalchemy import desc
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

    # แสดงเฉพาะทุนที่สถานะเปิด (open) และยังไม่หมดเขต (is_open)
    all_scholarships = Scholarship.query.filter_by(status='open').all()
    active_scholarships = [s for s in all_scholarships if s.is_open()]
    
    return render_template("student/dashboard.html", student=student, scholarships=active_scholarships)

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

            # Sync REG data (including name, faculty, etc.)
            student = RegService.sync_student_data(student, reg_data)
            student.set_password(input_password)

            # Set profile picture if missing (sync_student_data may already do it)
            if not student.profile_pic:
                student.profile_pic = "https://api.dicebear.com/9.x/initials/svg?seed=Student&radius=0&size=150"


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
        student_record.activity_hours  = int(request.form.get("activity_hours", 0))
        student_record.parttime_type   = request.form.get("parttime_type")

        student_record.exp_food      = safe_float("exp_food")
        student_record.exp_dorm      = safe_float("exp_dorm")
        student_record.exp_transport = safe_float("exp_transport")
        student_record.exp_other     = safe_float("exp_other")
        student_record.parttime_description = request.form.get("parttime_description", "").strip() or None
        db.session.commit()
        flash("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว ✅", "success")
        return redirect(url_for("student.profile"))
 
    
    # ดึงประวัติการรับทุน (รวมทุกสถานะที่ผ่านการอนุมัติ)
    success_statuses = ['approved', 'ได้รับทุน', 'Selected', 'อนุมัติ', 'completed', 'ได้รับทุนการศึกษา']
    

    # ถ้าต้องการ pagination (ตามปุ่มที่มีใน template) ให้ใช้ paginate()
    page = request.args.get('page', 1, type=int)
    # สำหรับ pagination
    pagination = Application.query.filter(
        Application.student_id == current_student_id,
        Application.status.in_(success_statuses)
    ).order_by(desc(Application.created_at)).paginate(page=page, per_page=5, error_out=False)
    apps = pagination.items

    return render_template("student/profile.html", 
                           student=student_record,
                           applications=apps,          # สำหรับแสดงในตาราง
                           pagination=pagination)      # สำหรับปุ่มก่อนหน้า/ถัดไป


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

    # ตรวจสอบว่าทุนเปิดอยู่หรือไม่ (Server-side check)
    if not scholarship.is_open() and not existing_app:
        flash("ขออภัย ทุนการศึกษานี้ปิดรับสมัครแล้ว หรือหมดเขตการรับสมัคร", "error")
        return redirect(url_for('student.dashboard'))

    # ตรวจสอบความสมบูรณ์ของโปรไฟล์และคุณสมบัติ
    profile_complete = False
    is_eligible = False
    eligibility_reasons = []

    if student:
        profile_complete = (student.profile_completeness == 100)
        is_eligible, eligibility_reasons = MatchingService.check_eligibility(student, scholarship)

    return render_template("student/scholarship_detail.html", 
                           scholarship=scholarship, 
                           student=student, 
                           already_applied=existing_app is not None,
                           existing_app=existing_app,
                           profile_complete=profile_complete,
                           is_eligible=is_eligible,
                           eligibility_reasons=eligibility_reasons)



# รับผิดชอบโดย: นาย จารุวัฒน์ บุญสาร
# ==========================================
# ฟีเจอร์: การสมัครทุนและจัดการไฟล์
# ==========================================

@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    housing_types = ["บ้านพัก", "ที่อยู่อาศัย", "ที่พัก"]
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("student.login"))

    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if request.method == "POST":
        # รับข้อมูลจากแบบฟอร์ม
        scholarship_id = request.form.get("scholarship_id")
        
        # ─── Server-side check: ทุนยังเปิดอยู่หรือไม่ ───
        target_scholarship = Scholarship.query.get(scholarship_id)
        if not target_scholarship or not target_scholarship.is_open():
            flash("ไม่สามารถส่งใบสมัครได้เนื่องจากทุนปิดรับสมัครแล้ว หรือหมดเขตแล้ว", "error")
            return redirect(url_for("student.dashboard"))
        
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
        
        # รวบรวมเหตุผลและหมายเหตุรายได้
        reason = request.form.get("reason", "").strip()
        income_note = request.form.get("income_note", "").strip()
        combined_notes = f"เหตุผลความจำเป็น: {reason}"
        if income_note:
            combined_notes += f"\n\nหมายเหตุรายได้: {income_note}"

        # บันทึกข้อมูลลงฐานข้อมูล Application
        new_app = Application(
            id=str(uuid.uuid4())[:12],
            student_id=current_student_id,
            student_name=student_name if student_name else student.name,
            faculty=faculty if faculty else student.faculty,
            scholarship_id=scholarship_id,
            status=status,
            activity_hours=int(request.form.get("activity_hours", 0)),
            parttime_type=request.form.get("parttime_type"),
            parttime_description=request.form.get("parttime_description", "").strip() or None,
            notes=combined_notes
        )
        
        # คณคะแนนอัตโนมัติทันที
        new_app.calculate_automatic_score()
        
        # อัปเดตข้อมูลกลับไปยังโปรไฟล์นักศึกษาด้วย (เพื่อให้ข้อมูลล่าสุดติดตัวนักศึกษาไป)
        if student:
            student.activity_hours = new_app.activity_hours
            student.parttime_type = new_app.parttime_type
            student.parttime_description = new_app.parttime_description
            student.inc_parttime = float(request.form.get("inc_parttime", 0) or 0)
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
    
    # GET method - แสดงเฉพาะทุนที่เปิดรับสมัครเท่านั้น
    scholarships = [s for s in Scholarship.query.filter_by(status='open').all() if s.is_open()]
    
    # ดึงข้อมูลนักศึกษามาแสดงไว้ก่อน (Prefill)
    prefill = {}
    if student:
        parts = student.name.split() if student.name else [""]
        title_val = ""
        if len(parts) >= 3 and parts[0] in ["นาย", "นาง", "นางสาว", "Mr.", "Ms.", "Mrs.", "ด.ช.", "ด.ญ."]:
            first_name = parts[1]
            last_name = " ".join(parts[2:])
            title_val = parts[0]
        else:
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            for t in ["นางสาว", "นาง", "นาย", "Mr.", "Ms.", "Mrs.", "ด.ช.", "ด.ญ."]:
                if first_name.startswith(t):
                    title_val = t
                    first_name = first_name[len(t):].strip()
                    break
        
        father_inc = getattr(student, 'father_income', None) or 0
        mother_inc = getattr(student, 'mother_income', None) or 0
        family_income = father_inc + mother_inc if (father_inc or mother_inc) else ""
        
        siblings_lst = getattr(student, 'siblings_list', None)
        siblings = len(siblings_lst) if siblings_lst else ""
        
        prefill = {
            "title": title_val,
            "student_id": student.student_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": getattr(student, 'email', ''),
            "faculty": student.faculty,
            "phone": getattr(student, 'mobile', ''),
            "address": getattr(student, 'address_current', ''),
            "father_name": getattr(student, 'father_name', ''),
            "father_occupation": getattr(student, 'father_job', ''),
            "father_income": getattr(student, 'father_income', ''),
            "mother_name": getattr(student, 'mother_name', ''),
            "mother_occupation": getattr(student, 'mother_job', ''),
            "mother_income": getattr(student, 'mother_income', ''),
            "year_level": getattr(student, 'year', ''),
            "gpa": getattr(student, 'gpax', ''),
            "housing_type": getattr(student, 'housing_status', ''),
            "family_income": family_income,
            "siblings": siblings,
            "siblings_list": siblings_lst if siblings_lst else [],
            "parents_status": getattr(student, 'parents_status', ''),
            "inc_father": getattr(student, 'inc_father', ''),
            "inc_mother": getattr(student, 'inc_mother', ''),
            "inc_guardian": getattr(student, 'inc_guardian', ''),
            "inc_scholarship": getattr(student, 'inc_scholarship', ''),
            "inc_parttime": getattr(student, 'inc_parttime', ''),
            "national_id": getattr(student, 'citizen_id', ''),
            "activity_hours": getattr(student, 'activity_hours', 0),
            "parttime_type": getattr(student, 'parttime_type', ''),
            "parttime_description": getattr(student, 'parttime_description', ''),
            "scholarship_id": request.args.get("scholarship_id"),
            "reason": "" # Default empty for new applications
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

# รับผิดชอบโดย: นาย จารุวัฒน์ บุญสาร
@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (เผื่อใช้รับไฟล์ผ่าน AJAX แยกต่างหาก)"""
    return "Student: Document Upload endpoint"

@student_bp.route("/scholarships")
def announce_scholarships():
    all_scholarships = Scholarship.query.all()
    
    recipients = {}
    for sch in all_scholarships:
        if sch.status in ['interview', 'announce']:
            # Fetch passing candidates for this scholarship
            apps = Application.query.filter(
                Application.scholarship_id == sch.id,
                Application.status.in_(['interview', 'approved', 'Selected', 'Reserved', 'อนุมัติ', 'completed'])
            ).all()
            recipients[sch.id] = apps

    return render_template("student/scholarships.html", scholarships=all_scholarships, recipients=recipients)


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
