from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Student, Scholarship
import json

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
        student_record.inc_parttime    = safe_float("inc_parttime")   # ✅ Part time

        # ── 9. ค่าใช้จ่ายนักศึกษาต่อเดือน ────────────────────────────
        student_record.exp_food       = safe_float("exp_food")
        student_record.exp_dorm       = safe_float("exp_dorm")
        student_record.exp_transport  = safe_float("exp_transport")
        student_record.exp_other      = safe_float("exp_other")

        # ── 10. กยศ. ──────────────────────────────────────────────────
        loan_raw = request.form.get("loan_student_fund", "FALSE")
        student_record.loan_student_fund = (loan_raw == "TRUE")
        # ถ้าไม่กู้ยืม → clear loan_type ด้วย
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
                    "income": str(s.get("income", "") or "").strip(),  # รายได้/เดือน
                }
                for s in parsed if isinstance(s, dict)
            ]
        except (json.JSONDecodeError, TypeError):
            pass  # ถ้า parse ไม่ได้ → คงค่าเดิม

        # ── 12. คำนวณ derived fields ──────────────────────────────────
        student_record.calculate_total_income()
        student_record.calculate_student_income()
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

    matches = MatchingService.get_all_matches(student)

    return render_template("student/auto_match.html",
                           student=student,
                           matches=matches)


# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อนสมัครทุน", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        return "สมัครทุนสำเร็จ (Logic ในการสร้าง Application Record)"

    scholarships = Scholarship.query.all()

    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

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
@student_bp.route('/logout')
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect('/')