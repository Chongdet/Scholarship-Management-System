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
            if siblings_data and siblings_data.strip():
                student_record.siblings_list = json.loads(siblings_data)
            
            scholarships_data = request.form.get("scholarships_json")
            if scholarships_data and scholarships_data.strip():
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
    return render_template("student/status.html")

@student_bp.route("/auto-match")
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ"""
    return render_template("student/auto_match.html")