from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Scholarship, Application
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# สร้าง Blueprint สำหรับ Student
student_bp = Blueprint('student', __name__)

# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ
# ==========================================

@student_bp.route('/dashboard')
def dashboard():
    """หน้าหลักของนักศึกษา (Student Dashboard)"""
    return render_template('student/dashboard.html')

@student_bp.route('/status')
def track_status():
    """ระบบติดตามสถานะการสมัคร (Application Status Tracking)"""
    return render_template('student/status.html')

@student_bp.route('/scholarships')
def list_scholarships():
    """หน้าประกาศทุนการศึกษา (Scholarship Announcement)"""
    return render_template('student/scholarships.html')



# ==========================================
# ผู้รับผิดชอบ: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
# ==========================================

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ระบบเข้าสู่ระบบและซิงค์ข้อมูล (Login & Data Synchronization)"""
    return "Student: Login and Data Sync"

@student_bp.route('/auto-match')
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ (Scholarship Auto-Matching)"""
    return "Student: Scholarship Auto-Matching Results"


# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

# ประเภทไฟล์ที่อนุญาตให้อัปโหลด
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE_MB = 5  # จำกัดขนาดไฟล์สูงสุด 5 MB


def allowed_file(filename):
    """ตรวจสอบนามสกุลไฟล์ว่าอยู่ในรายการที่อนุญาตหรือไม่"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@student_bp.route('/apply', methods=['GET', 'POST'])
def apply_scholarship():
    """ฟอร์มสมัครทุน (Application Form & Auto-Fill)

    GET  – แสดงฟอร์ม พร้อม Auto-Fill ข้อมูลจากใบสมัครล่าสุดของนักศึกษา (ถ้ามี)
    POST – บันทึกใบสมัครใหม่ลงฐานข้อมูล
    """
    scholarships = Scholarship.query.all()

    if request.method == 'POST':
        # --- ข้อมูลส่วนตัว ---
        title        = request.form.get('title', '').strip()
        first_name   = request.form.get('first_name', '').strip()
        last_name    = request.form.get('last_name', '').strip()
        first_name_en = request.form.get('first_name_en', '').strip()
        last_name_en  = request.form.get('last_name_en', '').strip()
        national_id  = request.form.get('national_id', '').strip()
        birth_date   = request.form.get('birth_date', '').strip()
        gender       = request.form.get('gender', '').strip()
        nationality  = request.form.get('nationality', '').strip()
        religion     = request.form.get('religion', '').strip()
        phone        = request.form.get('phone', '').strip()
        email        = request.form.get('email', '').strip()

        # --- ที่อยู่ ---
        address      = request.form.get('address', '').strip()
        sub_district = request.form.get('sub_district', '').strip()
        district     = request.form.get('district', '').strip()
        province     = request.form.get('province', '').strip()
        postal_code  = request.form.get('postal_code', '').strip()

        # --- การศึกษา ---
        student_id     = request.form.get('student_id', '').strip()
        faculty        = request.form.get('faculty', '').strip()
        major          = request.form.get('major', '').strip()
        year_level     = request.form.get('year_level', '').strip()
        gpa            = request.form.get('gpa', '').strip()
        academic_year  = request.form.get('academic_year', '').strip()

        # --- ผู้ปกครอง ---
        father_name       = request.form.get('father_name', '').strip()
        father_occupation = request.form.get('father_occupation', '').strip()
        father_income     = request.form.get('father_income', '').strip()
        father_phone      = request.form.get('father_phone', '').strip()
        father_status     = request.form.get('father_status', '').strip()
        mother_name       = request.form.get('mother_name', '').strip()
        mother_occupation = request.form.get('mother_occupation', '').strip()
        mother_income     = request.form.get('mother_income', '').strip()
        mother_phone      = request.form.get('mother_phone', '').strip()
        mother_status     = request.form.get('mother_status', '').strip()

        # --- รายได้ครอบครัว ---
        family_income  = request.form.get('family_income', '').strip()
        siblings       = request.form.get('siblings', '').strip()
        birth_order    = request.form.get('birth_order', '').strip()
        housing_type   = request.form.get('housing_type', '').strip()
        income_note    = request.form.get('income_note', '').strip()

        # --- ข้อมูลเพิ่มเติม ---
        prev_scholarship        = request.form.get('prev_scholarship', '').strip()
        prev_scholarship_detail = request.form.get('prev_scholarship_detail', '').strip()
        activities              = request.form.get('activities', '').strip()
        reason                  = request.form.get('reason', '').strip()

        scholarship_id = request.form.get('scholarship_id', type=int)

        # ชื่อเต็มสำหรับบันทึกลงฐานข้อมูล
        student_name = f"{title}{first_name} {last_name}".strip()

        # ---- ตรวจสอบข้อมูล ----
        errors = []
        if not student_id:
            errors.append('กรุณากรอกรหัสนักศึกษา')
        if not first_name or not last_name:
            errors.append('กรุณากรอกชื่อและนามสกุล')
        if not faculty:
            errors.append('กรุณาเลือกคณะ')
        if not gpa:
            errors.append('กรุณากรอกเกรดเฉลี่ย (GPA)')
        if not scholarship_id:
            errors.append('กรุณาเลือกทุนการศึกษาที่ต้องการสมัคร')
        if not reason:
            errors.append('กรุณาระบุเหตุผลที่ต้องการสมัครทุน')

        if student_id and scholarship_id:
            existing = Application.query.filter_by(
                student_id=student_id,
                scholarship_id=scholarship_id
            ).first()
            if existing:
                errors.append('คุณได้สมัครทุนนี้ไปแล้ว ไม่สามารถสมัครซ้ำได้')

        if errors:
            for err in errors:
                flash(err, 'error')
            prefill = request.form.to_dict()
            prefill['scholarship_id'] = scholarship_id
            return render_template('student/apply.html',
                                   scholarships=scholarships,
                                   prefill=prefill)

        # ---- บันทึกใบสมัคร ----
        today = datetime.today().strftime('%Y-%m-%d')
        new_application = Application(
            student_id=student_id,
            student_name=student_name,
            faculty=faculty,
            gpa=gpa,
            application_date=today,
            scholarship_id=scholarship_id,
            status='pending'
        )
        db.session.add(new_application)
        db.session.commit()

        flash(f'สมัครทุนสำเร็จแล้ว! รหัสการสมัคร: #{new_application.id}', 'success')
        return redirect(url_for('student.track_status'))

    # ---- GET: Auto-Fill ----
    prefill = {}
    last_app = Application.query.order_by(Application.id.desc()).first()
    if last_app:
        name_parts = last_app.student_name.split(' ', 1) if last_app.student_name else ['', '']
        prefill = {
            'student_id': last_app.student_id,
            'first_name': name_parts[0] if name_parts else '',
            'last_name':  name_parts[1] if len(name_parts) > 1 else '',
            'faculty':    last_app.faculty,
            'gpa':        last_app.gpa,
        }

    return render_template('student/apply.html',
                           scholarships=scholarships,
                           prefill=prefill)


@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (Document Upload)
    
    รับไฟล์ PDF / รูปภาพ (PNG, JPG, JPEG) ขนาดไม่เกิน 5 MB
    บันทึกไฟล์ไว้ที่ static/uploads/<student_id>/
    """
    student_id = request.form.get('student_id', 'unknown').strip()
    files = request.files.getlist('documents')

    if not files or all(f.filename == '' for f in files):
        flash('กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์', 'error')
        return redirect(url_for('student.apply_scholarship'))

    # สร้างโฟลเดอร์สำหรับเก็บเอกสารของนักศึกษาคนนี้
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', student_id)
    os.makedirs(upload_dir, exist_ok=True)

    saved_files = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        # ตรวจสอบนามสกุลไฟล์
        if not allowed_file(file.filename):
            errors.append(f'"{file.filename}" — รองรับเฉพาะ PDF, PNG, JPG, JPEG เท่านั้น')
            continue

        # ตรวจสอบขนาดไฟล์ (อ่านก้อนแรกแล้วค่อย seek กลับ)
        file.seek(0, os.SEEK_END)
        file_size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if file_size_mb > MAX_FILE_SIZE_MB:
            errors.append(f'"{file.filename}" — ขนาดไฟล์เกิน {MAX_FILE_SIZE_MB} MB')
            continue

        # บันทึกไฟล์
        filename = secure_filename(file.filename)
        save_path = os.path.join(upload_dir, filename)
        file.save(save_path)
        saved_files.append(filename)

    if errors:
        for err in errors:
            flash(err, 'error')

    if saved_files:
        flash(f'อัปโหลดสำเร็จ {len(saved_files)} ไฟล์: {", ".join(saved_files)}', 'success')

    return redirect(url_for('student.apply_scholarship'))