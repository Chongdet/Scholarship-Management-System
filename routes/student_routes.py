from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models import db, Scholarship, Application, Student
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

student_bp = Blueprint('student', __name__)

# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ & นาย กิตติพงษ์
# ฟีเจอร์: Dashboard & Login
# ==========================================

@student_bp.route('/dashboard')
def dashboard():
    if 'user_data' not in session:
        return redirect(url_for('student.login'))
    
    student = session.get('user_data')
    return render_template('student/dashboard.html', student=student)

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # จำลองข้อมูล Login (ในอนาคตควร Query จากฐานข้อมูล Student)
        user_info = {
            "student_id": "68113400123",
            "name": "นางสาวมณี มีหวัง",
            "gpax": 2.85,
            "faculty": "คณะวิศวกรรมศาสตร์",
            "email": "manee.m.68@ubu.ac.th",
            "phone": "098-765-4321",
            "parents_status": "บิดามารดาอยู่ด้วยกัน",
            "family_income": 7000
        }
        session['user_data'] = user_info
        session['user_id'] = user_info['student_id']
        
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/login.html')

# ==========================================
# ผู้รับผิดชอบ: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
# ฟีเจอร์: Profile Management (จัดการข้อมูล JSON)
# ==========================================

@student_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('student.login'))
    
    current_student_id = session['user_id']
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    # สร้างข้อมูลตั้งต้นถ้ายังไม่มีใน DB
    if not student_record:
        user_data = session.get('user_data', {})
        student_record = Student(
            student_id=current_student_id,
            name=user_data.get('name', 'ไม่ระบุชื่อ'),
            email=user_data.get('email', ''),
            faculty=user_data.get('faculty', ''),
            gpax=user_data.get('gpax', 0.0),
            citizen_id="1341500289xxx",
            year=1,
            advisor_name="ผศ.ดร.สมชาย ใจดี",
            disciplinary_status="Normal",
            address_domicile="อุบลราชธานี",
            father_name="นายมานะ มีหวัง",
            mother_name="นางมาลี มีหวัง"
        )
        db.session.add(student_record)
        db.session.commit()

    if request.method == 'POST':
        # อัปเดตข้อมูลจากการกรอกฟอร์ม
        student_record.mobile = request.form.get('mobile', student_record.mobile)
        student_record.facebook = request.form.get('facebook', student_record.facebook)
        student_record.line_id = request.form.get('line_id', student_record.line_id)
        student_record.address_current = request.form.get('address_current', student_record.address_current)
        
        student_record.loan_student_fund = True if request.form.get('loan_student_fund') == 'TRUE' else False
        student_record.loan_type = request.form.get('loan_type', '')
        
        # จัดการข้อมูล JSON
        siblings_data = request.form.get('siblings_json')
        if siblings_data:
            try:
                student_record.siblings_list = json.loads(siblings_data)
            except: pass

        db.session.commit()
        flash('อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student_record)

# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ฟีเจอร์: Apply Scholarship & Upload
# ==========================================

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE_MB = 5

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route('/apply', methods=['GET', 'POST'])
def apply_scholarship():
    scholarships = Scholarship.query.all()
    # ... (Logic การ Apply ตามที่คุณจารุวัฒน์เขียนไว้ด้านบน) ...
    # หมายเหตุ: โค้ดส่วนนี้ยาว Lead สามารถใช้ของเดิมที่คุณจารุวัฒน์เขียนได้เลยครับ
    return render_template('student/apply.html', scholarships=scholarships)

@student_bp.route('/status')
def track_status():
    return render_template('student/status.html') # แก้ให้เรียก template

@student_bp.route('/auto-match')
def auto_match():
    return "Student: Scholarship Auto-Matching Results"