from flask import Blueprint, render_template, request

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

@student_bp.route('/apply', methods=['GET', 'POST'])
def apply_scholarship():
    """ฟอร์มสมัครทุน (Application Form & Auto-Fill)"""
    return "Student: Application Form (Auto-Fill enabled)"

@student_bp.route('/upload', methods=['POST'])
def upload_documents():
    """อัปโหลดเอกสารประกอบการสมัคร (InputDocument Upload)"""
    return "Student: Document Upload endpoint"