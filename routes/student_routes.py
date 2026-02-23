from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Student, Scholarship  # 🌟 1. เพิ่ม Scholarship เข้ามาที่นี่
import json

student_bp = Blueprint("student", __name__)

# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ
# ==========================================

@student_bp.route("/dashboard")
def dashboard():
    # ตรวจสอบการ Login
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("login"))

    # ดึงข้อมูลนักศึกษาที่ Login
    current_student_id = session["user_id"]
    student = Student.query.filter_by(student_id=current_student_id).first()

    if not student:
        flash("ไม่พบข้อมูลนักศึกษา", "error")
        return redirect(url_for("login"))

    # 🌟 2. ดึงข้อมูลทุนทั้งหมดจาก Database มาแสดงให้นักศึกษาเห็น
    all_scholarships = Scholarship.query.all()

    # 🌟 3. ส่ง scholarships=all_scholarships ไปที่ Template
    return render_template("student/dashboard.html", 
                           student=student, 
                           scholarships=all_scholarships)


@student_bp.route("/status")
def track_status():
    """ระบบติดตามสถานะการสมัคร (Application Status Tracking)"""
    return "Student: Application Status"


# ==========================================
# ผู้รับผิดชอบ: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
# ==========================================

@student_bp.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for("login"))


@student_bp.route("/auto-match")
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ (Scholarship Auto-Matching)"""
    return "Student: Scholarship Auto-Matching Results"


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
        # อัปเดตข้อมูลส่วนตัว
        student_record.mobile = request.form.get("mobile", student_record.mobile)
        student_record.facebook = request.form.get("facebook", student_record.facebook)
        student_record.line_id = request.form.get("line_id", student_record.line_id)
        student_record.address_current = request.form.get("address_current", student_record.address_current)

        # ข้อมูลกู้ยืม
        student_record.loan_student_fund = True if request.form.get("loan_student_fund") == "TRUE" else False
        student_record.loan_type = request.form.get("loan_type", "")

        # รายได้และอาชีพ
        student_record.inc_father = request.form.get("inc_father", type=float, default=0.0)
        student_record.inc_mother = request.form.get("inc_mother", type=float, default=0.0)
        student_record.inc_guardian = request.form.get("inc_guardian", type=float, default=0.0)
        student_record.father_job = request.form.get("father_job", student_record.father_job)
        student_record.mother_job = request.form.get("mother_job", student_record.mother_job)
        student_record.parents_status = request.form.get("parents_status", student_record.parents_status)
        student_record.housing_status = request.form.get("housing_status", student_record.housing_status)
        student_record.land_status = request.form.get("land_status", student_record.land_status)
        student_record.land_size = request.form.get("land_size", type=float, default=0.0)

        # จัดการข้อมูล JSON
        siblings_data = request.form.get("siblings_json")
        if siblings_data:
            try: student_record.siblings_list = json.loads(siblings_data)
            except: pass

        scholarships_data = request.form.get("scholarships_json")
        if scholarships_data:
            try: student_record.scholarship_history = json.loads(scholarships_data)
            except: pass

        db.session.commit()
        flash("อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student_record)


# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    """ฟอร์มสมัครทุน"""
    return "Student: Application Form (Auto-Fill enabled)"

@student_bp.route("/upload", methods=["POST"])
def upload_documents():
    """อัปโหลดเอกสาร"""
    return "Student: Document Upload endpoint"