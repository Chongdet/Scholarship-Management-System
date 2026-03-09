import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, current_app, render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from models import db, Student, Scholarship, Application
from services.reg_service import RegService
from services.matching_service import MatchingService

student_bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# Dashboard & Landing
# ==========================================
@student_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "student":
        flash("กรุณาเข้าสู่ระบบ", "error")
        return redirect(url_for("student.login"))

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

            flash(f"เข้าสู่ระบบสำเร็จ! อัปเดตข้อมูลจาก REG เรียบร้อย", "success")
            return redirect(url_for('student.dashboard'))
        else:
            flash(f"การเข้าสู่ระบบล้มเหลว: {message}", "error")
    
    return render_template('login.html')

@student_bp.route('/logout')
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect(url_for("student.login"))

# ==========================================
# Profile Management
# ==========================================
@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("student.login"))

    current_student_id = session["user_id"]
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    if request.method == "POST":
        def safe_float(key, default=None):
            val = request.form.get(key, '').strip()
            try:
                return float(val) if val != '' else default
            except:
                return default

        # อัปเดตข้อมูลส่วนตัว
        student_record.mobile = request.form.get("mobile", "").strip() or None
        student_record.facebook = request.form.get("facebook", "").strip() or None
        student_record.address_current = request.form.get("address_current", "").strip() or None
        
        # ข้อมูลครอบครัว
        student_record.father_name = request.form.get("father_name")
        student_record.father_income = safe_float("father_income")
        student_record.mother_name = request.form.get("mother_name")
        student_record.mother_income = safe_float("mother_income")
        student_record.parents_status = request.form.get("parents_status")

        # จัดการข้อมูลพี่น้อง (JSON)
        try:
            siblings_data = request.form.get("siblings_json")
            if siblings_data:
                student_record.siblings_list = json.loads(siblings_data)
        except Exception as e:
            print(f"JSON Error: {e}")

        db.session.commit()
        flash("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว ✅", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student_record)

# ==========================================
# Scholarship Matching & Application
# ==========================================
@student_bp.route('/auto-match')
def auto_match():
    if "user_id" not in session:
        return redirect(url_for("student.login"))
    
    student = Student.query.filter_by(student_id=session["user_id"]).first()
    matches = MatchingService.get_all_matches(student)
    return render_template("student/auto_match.html", student=student, matches=matches)

@student_bp.route("/scholarships/<scholarship_id>")
def scholarship_detail(scholarship_id):
    if "user_id" not in session:
        return redirect(url_for("student.login"))

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

@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    if "user_id" not in session:
        return redirect(url_for("student.login"))

    student = Student.query.filter_by(student_id=session["user_id"]).first()

    if request.method == "POST":
        scholarship_id = request.form.get("scholarship_id")
        action = request.form.get("action", "submit")
        
        status = "draft" if action == "save_draft" else "pending"
        
        new_app = Application(
            id=f"APP-{student.student_id}-{scholarship_id}-{uuid.uuid4().hex[:4]}",
            student_id=student.student_id,
            scholarship_id=scholarship_id,
            status=status
        )
        
        # การจัดการไฟล์
        file = request.files.get("document")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{new_app.id}_{filename}"
            upload_path = os.path.join(current_app.static_folder, 'uploads', student.student_id)
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, unique_name))
            new_app.application_file = unique_name

        db.session.add(new_app)
        db.session.commit()
        flash("ส่งใบสมัครเรียบร้อยแล้ว", "success")
        return redirect(url_for("student.track_status"))

    scholarships = Scholarship.query.all()
    return render_template("student/apply.html", scholarships=scholarships, student=student)

@student_bp.route("/status")
def track_status():
    student_id = session.get("user_id")
    if not student_id:
        return redirect(url_for("student.login"))

    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template("student/status.html", applications=applications)