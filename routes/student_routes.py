from flask import Blueprint, render_template, request, session, redirect, url_for
from models import db, Student
import json

student_bp = Blueprint('student', __name__)

# ==========================================
# ผู้รับผิดชอบ: นางสาว ปัญญาพร มูลดับ
# ==========================================

@student_bp.route('/dashboard')
def dashboard():
    if 'user_data' not in session:
        return redirect(url_for('student.login'))
    
    student = session.get('user_data')

    return render_template('student/dashboard.html', student=student)

@student_bp.route('/status')
def track_status():
    """ระบบติดตามสถานะการสมัคร (Application Status Tracking)"""
    return "Student: Application Status"


# ==========================================
# ผู้รับผิดชอบ: นาย กิตติพงษ์ เลี้ยงหิรัญถาวร
# ==========================================
# แก้ไขส่วนของคุณ กิตติพงษ์
@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
        
        # แก้จาก student.profile เป็น student.dashboard ตามที่ต้องการ 🚀
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/login.html')

# แก้ไขส่วนของคุณ ปัญญาพร (เพื่อให้ UI ขึ้น)



@student_bp.route('/auto-match')
def auto_match():
    """ระบบจับคู่ทุนอัตโนมัติ (Scholarship Auto-Matching)"""
    return "Student: Scholarship Auto-Matching Results"


@student_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('student.login'))
    
    current_student_id = session['user_id']
    student_record = Student.query.filter_by(student_id=current_student_id).first()

    # สร้างข้อมูลตั้งต้น (จำลองการดึงข้อมูลจาก REG มาใส่ Database กรณีล็อกอินครั้งแรก)
    if not student_record:
        user_data = session.get('user_data', {})
        student_record = Student(
            student_id=current_student_id,
            name=user_data.get('name', 'ไม่ระบุชื่อ'),
            email=user_data.get('email', ''),
            faculty=user_data.get('faculty', ''),
            gpax=user_data.get('gpax', 0.0),
            # จำลองข้อมูล REG อื่นๆ 
            citizen_id="1341500289xxx",
            year=1,
            advisor_name="ผศ.ดร.สมชาย ใจดี",
            disciplinary_status="Normal (ไม่เคยทำผิดวินัย)",
            address_domicile="45 หมู่ 3 ต.ไร่น้อย อ.เมือง จ.อุบลราชธานี 34000",
            father_name="นายมานะ มีหวัง",
            mother_name="นางมาลี มีหวัง"
        )
        db.session.add(student_record)
        db.session.commit()

    if request.method == 'POST':
        # --- 1. ข้อมูลส่วนตัวและการติดต่อ (อัปเดตเฉพาะช่องที่อนุญาต) ---
        student_record.mobile = request.form.get('mobile', student_record.mobile)
        student_record.facebook = request.form.get('facebook', student_record.facebook)
        student_record.line_id = request.form.get('line_id', student_record.line_id)
        student_record.address_current = request.form.get('address_current', student_record.address_current)
        # ❌ ตัด name, citizen_id, email, address_domicile ออก เพราะมาจาก REG

        # --- 2. ข้อมูลการศึกษา ---
        # ❌ ตัด faculty, year, gpax, advisor, disciplinary ออก เพราะมาจาก REG

        # --- 3. ประวัติการขอทุนและกู้ยืม ---
        student_record.loan_student_fund = True if request.form.get('loan_student_fund') == 'TRUE' else False
        student_record.loan_type = request.form.get('loan_type', '')

        # --- 4. ข้อมูลครอบครัวและรายได้ ---
        student_record.inc_father = request.form.get('inc_father', type=float, default=0.0)
        student_record.inc_mother = request.form.get('inc_mother', type=float, default=0.0)
        student_record.inc_guardian = request.form.get('inc_guardian', type=float, default=0.0)
        
        # ❌ ตัด father_name และ mother_name ออก เพราะมาจาก REG
        student_record.father_job = request.form.get('father_job', student_record.father_job)
        student_record.father_income = request.form.get('father_income', type=float, default=0.0)
        student_record.father_health = request.form.get('father_health', student_record.father_health)

        student_record.mother_job = request.form.get('mother_job', student_record.mother_job)
        student_record.mother_income = request.form.get('mother_income', type=float, default=0.0)

        student_record.parents_status = request.form.get('parents_status', student_record.parents_status)
        student_record.housing_status = request.form.get('housing_status', student_record.housing_status)
        student_record.land_status = request.form.get('land_status', student_record.land_status)
        student_record.land_size = request.form.get('land_size', type=float, default=0.0)
        
        # --- 5. จัดการข้อมูล JSON (พี่น้อง และ ประวัติทุน) ---
        siblings_data = request.form.get('siblings_json')
        if siblings_data:
            try:
                student_record.siblings_list = json.loads(siblings_data)
            except Exception as e:
                print("Error parsing siblings:", e)

        scholarships_data = request.form.get('scholarships_json')
        if scholarships_data:
            try:
                student_record.scholarship_history = json.loads(scholarships_data)
            except Exception as e:
                print("Error parsing scholarships:", e)

        db.session.commit()
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student_record)


# ==========================================
# ผู้รับผิดชอบ: นาย จารุวัฒน์ บุญสาร
# ==========================================

@student_bp.route('/apply', methods=['GET', 'POST'])
def apply_scholarship():
    """ฟอร์มสมัครทุน (Application Form & Auto-Fill)"""
    return "Student: Application Form (Auto-Fill enabled)"

@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (InputDocument Upload)"""
    return "Student: Document Upload endpoint"