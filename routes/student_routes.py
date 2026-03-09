from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Student, Scholarship
import json
<<<<<<< HEAD
=======
import uuid

from flask import Blueprint, current_app, render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from models import db, Student, Scholarship, Application
from services.reg_service import RegService
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

student_bp = Blueprint('student', __name__)


# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ
# ==========================================
@student_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("login"))

    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("login"))

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

<<<<<<< HEAD
        # ── Helper: แปลง float ปลอดภัย (รับ '' และ None ได้) ──────────
=======
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)
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
        student_record.mobile          = request.form.get("mobile",   "").strip() or None
        student_record.facebook        = request.form.get("facebook", "").strip() or None
        student_record.line_id         = request.form.get("line_id",  "").strip() or None
        student_record.address_current = request.form.get("address_current", "").strip() or None

        # ── 2. บิดา ───────────────────────────────────────────────────
        student_record.father_name   = request.form.get("father_name",   "").strip() or None
        student_record.father_job    = request.form.get("father_job",    "").strip() or None
        student_record.father_income = safe_float("father_income")
        student_record.inc_father    = safe_float("inc_father")
        student_record.father_health = request.form.get("father_health", "").strip() or None

        # ── 3. มารดา ──────────────────────────────────────────────────
        student_record.mother_name   = request.form.get("mother_name",   "").strip() or None
        student_record.mother_job    = request.form.get("mother_job",    "").strip() or None
        student_record.mother_income = safe_float("mother_income")
        student_record.inc_mother    = safe_float("inc_mother")
        student_record.mother_health = request.form.get("mother_health", "").strip() or None

        # ── 4. สถานภาพสมรสบิดา-มารดา ─────────────────────────────────
        student_record.parents_status = request.form.get("parents_status") or None

        # ── 5. ที่อยู่อาศัย ───────────────────────────────────────────
        student_record.housing_status = request.form.get("housing_status") or None
        student_record.rent_amount    = safe_float("rent_amount")
        student_record.housing_other  = request.form.get("housing_other", "").strip() or None

        # ── 6. ที่ดินเกษตร ────────────────────────────────────────────
        student_record.land_status        = request.form.get("land_status") or None
        student_record.agri_own_amount    = safe_float("agri_own_amount")
        student_record.agri_rent_amount   = safe_float("agri_rent_amount")
        student_record.agri_rent_cost     = safe_float("agri_rent_cost")
        student_record.agri_other_detail  = request.form.get("agri_other_detail", "").strip() or None

        # ── 7. ผู้อุปการะ ─────────────────────────────────────────────
        student_record.guardian_name     = request.form.get("guardian_name",     "").strip() or None
        student_record.guardian_relation = request.form.get("guardian_relation", "").strip() or None
        student_record.guardian_job      = request.form.get("guardian_job",      "").strip() or None
        student_record.guardian_income   = safe_float("guardian_income")

        # ── 8. รายได้ที่นักศึกษาได้รับต่อเดือน ───────────────────────
        student_record.inc_guardian    = safe_float("inc_guardian")
        student_record.inc_scholarship = safe_float("inc_scholarship")
<<<<<<< HEAD
        student_record.inc_parttime    = safe_float("inc_parttime")   # ✅ Part time
=======
        student_record.inc_parttime    = safe_float("inc_parttime")
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

        # ── 9. ค่าใช้จ่ายนักศึกษาต่อเดือน ────────────────────────────
        student_record.exp_food       = safe_float("exp_food")
        student_record.exp_dorm       = safe_float("exp_dorm")
        student_record.exp_transport  = safe_float("exp_transport")
        student_record.exp_other      = safe_float("exp_other")

        # ── 10. กยศ. ──────────────────────────────────────────────────
        loan_raw = request.form.get("loan_student_fund", "FALSE")
        student_record.loan_student_fund = (loan_raw == "TRUE")
<<<<<<< HEAD
        # ถ้าไม่กู้ยืม → clear loan_type ด้วย
=======
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)
        if loan_raw == "FALSE":
            student_record.loan_type = None
        else:
            student_record.loan_type = request.form.get("loan_type") or None

        # ── 11. พี่น้อง (รับ JSON จาก hidden field) ───────────────────
        try:
            siblings_raw = request.form.get("siblings_json", "[]").strip()
            parsed = json.loads(siblings_raw)
            student_record.siblings_list = [
                {
                    "name":   str(s.get("name",   "") or "").strip(),
                    "age":    str(s.get("age",    "") or "").strip(),
                    "job":    str(s.get("job",    "") or "").strip(),
                    "place":  str(s.get("place",  "") or "").strip(),
<<<<<<< HEAD
                    "income": str(s.get("income", "") or "").strip(),  # รายได้/เดือน
=======
                    "income": str(s.get("income", "") or "").strip(),
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)
                }
                for s in parsed if isinstance(s, dict)
            ]
        except (json.JSONDecodeError, TypeError):
<<<<<<< HEAD
            pass  # ถ้า parse ไม่ได้ → คงค่าเดิม
=======
            pass
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

        # ── 12. คำนวณ derived fields ──────────────────────────────────
        student_record.calculate_total_income()
        student_record.calculate_student_income()
        student_record.update_completeness()

        db.session.commit()
        flash("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว ✅", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student_record)


# ==========================================
# ฟีเจอร์: Auto-Match ทุนการศึกษา
# ==========================================
@student_bp.route('/auto-match')
def auto_match():
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
<<<<<<< HEAD
        return redirect(url_for("login"))
=======
        return redirect(url_for("student.login"))
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

    from services.matching_service import MatchingService
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
<<<<<<< HEAD
        return redirect(url_for("login"))
=======
        return redirect(url_for("student.login"))
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

    matches = MatchingService.get_all_matches(student)

    return render_template("student/auto_match.html",
                           student=student,
                           matches=matches)


# ==========================================
# ฟีเจอร์: รายละเอียดทุน + ตรวจสอบสิทธิ์ (FR-02)
# ==========================================
@student_bp.route("/scholarships/<scholarship_id>")
def scholarship_detail(scholarship_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("student.login"))

    scholarship = Scholarship.query.get_or_404(scholarship_id)
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    # ตรวจสอบว่าเคยสมัครแล้วหรือยัง
    existing_app = Application.query.filter_by(
        student_id=current_student_id,
        scholarship_id=scholarship_id
    ).first()

    # ── Auto-Matching: ตรวจสอบสิทธิ์ ──────────────────────────────
    eligibility_reasons = []
    is_eligible = True

    if student:
        # เช็ค GPAX ขั้นต่ำ
        min_gpax = getattr(scholarship, 'min_gpax', None)
        if min_gpax:
            if student.gpax is not None:
                if student.gpax < min_gpax:
                    is_eligible = False
                    eligibility_reasons.append(
                        f"เกรดเฉลี่ยสะสม (GPAX) ของคุณ {student.gpax:.2f} ต่ำกว่าเกณฑ์ขั้นต่ำ {min_gpax:.2f}"
                    )
            else:
                is_eligible = False
                eligibility_reasons.append("ไม่พบข้อมูล GPAX ในระบบ")

        # เช็ค Faculty — ใช้ getattr ป้องกัน field ไม่มีใน model
        sch_faculty = getattr(scholarship, 'faculty', None)
        if sch_faculty and student.faculty:
            if sch_faculty not in student.faculty:
                is_eligible = False
                eligibility_reasons.append(
                    f"ทุนนี้เปิดรับเฉพาะ {sch_faculty} เท่านั้น"
                )

        # เช็ค ชั้นปี — ใช้ getattr ป้องกัน field ไม่มีใน model
        sch_year = getattr(scholarship, 'year', None)
        if sch_year and student.year:
            if str(student.year) != str(sch_year):
                is_eligible = False
                eligibility_reasons.append(
                    f"ทุนนี้รับเฉพาะนักศึกษาชั้นปีที่ {sch_year}"
                )

    # ── ตรวจสอบความครบถ้วนของโปรไฟล์ ──────────────────────────────
    profile_complete = False
    if student:
        completeness = getattr(student, 'profile_completeness', None)
        if completeness is not None:
            profile_complete = completeness >= 80
        else:
            # fallback: เช็ค field สำคัญขั้นต่ำ
            profile_complete = bool(
                student.mobile and student.father_name and student.mother_name
            )

    return render_template("student/scholarship_detail.html",
                           scholarship=scholarship,
                           student=student,
                           already_applied=existing_app is not None,
                           existing_app=existing_app,
                           is_eligible=is_eligible,
                           eligibility_reasons=eligibility_reasons,
                           profile_complete=profile_complete)


# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
<<<<<<< HEAD
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อนสมัครทุน", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        return "สมัครทุนสำเร็จ (Logic ในการสร้าง Application Record)"

    scholarships = Scholarship.query.all()
=======
    housing_types = ["บ้านพัก", "ที่อยู่อาศัย", "ที่พัก"]

    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("student.login"))
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)

    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

<<<<<<< HEAD
    prefill_data = {
        'student_id': student.student_id if student else '',
        'first_name': student.name.split()[0] if student and student.name else '',
        'last_name':  student.name.split()[1] if student and student.name and len(student.name.split()) > 1 else '',
        'faculty':    student.faculty if student else '',
    }

    return render_template("student/apply.html",
                           scholarships=scholarships,
                           prefill=prefill_data)


@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร"""
    return "Student: Document Upload endpoint"


# ==========================================
# ฟีเจอร์: ออกจากระบบ (Logout)
# ==========================================
=======
    if request.method == "POST":
        scholarship_id = request.form.get("scholarship_id")
        action         = request.form.get("action", "submit")

        first_name   = request.form.get("first_name", "")
        last_name    = request.form.get("last_name", "")
        student_name = f"{first_name} {last_name}".strip()
        faculty      = request.form.get("faculty", "")

        if not scholarship_id:
            flash("กรุณาเลือกทุนการศึกษา", "error")
            return redirect(url_for("student.apply_scholarship"))

        # ตรวจสอบว่าเคยสมัครทุนนี้หรือยัง
        existing_app = Application.query.filter_by(
            student_id=current_student_id,
            scholarship_id=scholarship_id
        ).first()
        if existing_app:
            flash("คุณได้สมัครทุนนี้ไปแล้ว", "error")
            return redirect(url_for("student.dashboard"))

        status = "draft" if action == "save_draft" else "pending"

        new_app = Application(
            id=f"APP-{current_student_id}-{scholarship_id}",
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

        flash("บันทึกข้อมูลการสมัครเรียบร้อยแล้ว", "success")
        # กลับหน้า detail พร้อม trigger pop-up สำเร็จ
        return redirect(
            url_for("student.scholarship_detail", scholarship_id=scholarship_id) + "?applied=success"
        )

    # GET — แสดงฟอร์มสมัคร
    scholarships = Scholarship.query.all()

    prefill = {}
    if student:
        parts      = student.name.split() if student.name else [""]
        first_name = parts[0]
        last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""
        prefill = {
            "student_id": student.student_id,
            "first_name": first_name,
            "last_name":  last_name,
            "email":      student.email,
            "faculty":    student.faculty
        }

    titles         = ["นาย", "นางสาว", "นาง"]
    genders        = ["ชาย", "หญิง"]
    faculties      = [
        "คณะเกษตรศาสตร์", "คณะวิทยาศาสตร์", "คณะวิศวกรรมศาสตร์", "คณะศิลปศาสตร์",
        "คณะเภสัชศาสตร์", "คณะบริหารศาสตร์", "คณะพยาบาลศาสตร์",
        "วิทยาลัยแพทยศาสตร์และการสาธารณสุข", "คณะศิลปประยุกต์และสถาปัตยกรรมศาสตร์",
        "คณะนิติศาสตร์", "คณะรัฐศาสตร์"
    ]
    year_levels    = [1, 2, 3, 4, 5, 6]
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


>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)
@student_bp.route('/logout')
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
<<<<<<< HEAD
    return redirect('/')
=======
    return redirect(url_for("student.login"))


@student_bp.route("/status")
def track_status():
    student_id = session.get("user_id")
    if not student_id:
        return redirect(url_for("student.login"))

    page       = request.args.get('page', 1, type=int)
    pagination = Application.query.filter_by(student_id=student_id)\
        .order_by(Application.created_at.desc())\
        .paginate(page=page, per_page=5, error_out=False)

    for app in pagination.items:
        user_upload_dir = os.path.join(current_app.static_folder, 'uploads', str(student_id))
        app.all_files   = []
        if os.path.exists(user_upload_dir):
            all_entries   = os.listdir(user_upload_dir)
            app.all_files = [f for f in all_entries if f.startswith(f"app_{app.id}")]

    return render_template("student/status.html", pagination=pagination)


@student_bp.route("/status/detail/<app_id>")
def status_detail(app_id):
    if "user_id" not in session:
        return redirect(url_for("student.login"))

    application = Application.query.get_or_404(app_id)
    return render_template("student/status_detail.html", app=application)


@student_bp.route("/scholarships")
def announce_scholarships():
    all_scholarships = Scholarship.query.all()
    return render_template("student/scholarships.html", scholarships=all_scholarships)
>>>>>>> 8eaf5c2 (แก้ไข student routes และหน้า dashboard/profile)
