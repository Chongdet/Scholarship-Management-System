from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from models import db, Scholarship, Application, Student
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

student_bp = Blueprint('student', __name__)


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

    return render_template(
        "student/dashboard.html", student=student, scholarships=all_scholarships
    )


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
        student_record.address_current = request.form.get(
            "address_current", student_record.address_current
        )

        # 2. ข้อมูลสถานะการกู้ยืมและครอบครัว
        student_record.loan_student_fund = (
            True if request.form.get("loan_student_fund") == "TRUE" else False
        )
        student_record.loan_type = request.form.get("loan_type", "")
        student_record.parents_status = request.form.get(
            "parents_status", student_record.parents_status
        )

        # 3. ข้อมูลรายได้ (รองรับทศนิยม)
        student_record.inc_father = request.form.get(
            "inc_father", type=float, default=0.0
        )
        student_record.inc_mother = request.form.get(
            "inc_mother", type=float, default=0.0
        )
        student_record.inc_guardian = request.form.get(
            "inc_guardian", type=float, default=0.0
        )

        # 4. จัดการข้อมูล JSON (พี่น้อง และ ประวัติทุน)
        try:
            siblings_data = request.form.get("siblings_json")
            if siblings_data:
                student_record.siblings_list = json.loads(siblings_data)

            scholarships_data = request.form.get("scholarships_json")
            if scholarships_data:
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
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@student_bp.route("/apply", methods=["GET", "POST"])
def apply_scholarship():
    if request.method == "POST":
        scholarship_id = request.form.get('scholarship_id')
        student_id = session.get('user_id') 

        # 1. จัดการรับไฟล์จากฟอร์ม (ตาม name ที่ตั้งใน HTML)
        files = {
            'transcript': request.files.get('file_transcript'),
            'id_card': request.files.get('file_id_card'),
            'income': request.files.get('file_income_cert'),
            'house': request.files.getlist('file_house_pics') # รับแบบ List เพราะอัปโหลดได้หลายรูป
        }

        # 2. ตัวอย่าง Logic การบันทึกไฟล์ (คุณต้องสร้างโฟลเดอร์ uploads รอไว้)
        # file_paths = {}
        # for key, file in files.items():
        #     if file and file.filename != '':
        #         filename = secure_filename(f"{student_id}_{key}_{file.filename}")
        #         file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        #         file_paths[key] = filename

        # 3. *** บันทึกลง Database ***
        # new_application = Application(
        #     student_id=student_id,
        #     scholarship_id=scholarship_id,
        #     transcript_path=file_paths.get('transcript'),
        #     status='pending'
        # )
        # db.session.add(new_application)
        # db.session.commit() # บรรทัดนี้สำคัญมาก ถ้าไม่มีข้อมูลจะไม่ลง DB

        flash("ยื่นใบสมัครและอัปโหลดเอกสารเรียบร้อยแล้ว!", "success")
        return redirect(url_for("student.apply_scholarship"))

    # ส่วน GET: ดึงข้อมูลมาแสดงหน้าฟอร์ม
    scholarships = Scholarship.query.all()
    # ดึง ID ทุนที่นักเรียนคนนี้เคยสมัครแล้วจริงๆ จาก DB
    # applied_ids = [app.scholarship_id for app in Application.query.filter_by(student_id=session.get('user_id')).all()]
    applied_ids = [] # ใส่ผลลัพธ์จาก Query ด้านบนแทน

    return render_template("student/apply.html", 
                           scholarships=scholarships, 
                           applied_ids=applied_ids)


@student_bp.route("/status")
def track_status():
    """ระบบติดตามสถานะการสมัคร"""
    return render_template("student/status.html")


@student_bp.route("/auto-match")
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ"""
    return render_template("student/auto_match.html")
