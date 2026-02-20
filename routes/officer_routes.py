from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Application, Scholarship

# สร้าง Blueprint สำหรับ Officer
officer_bp = Blueprint('officer', __name__)

# ==========================================
# ผู้รับผิดชอบ: นาย ยศสรัล ถิระบุตร
# ==========================================

@officer_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ระบบเข้าสู่ระบบของเจ้าหน้าที่ (Officer Login)"""
    return "Officer: Login Page"

@officer_bp.route('/scholarships', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_scholarships():
    """ระบบจัดการทุนการศึกษา (Scholarship Management)"""
    return "Officer: Scholarship Management System"


# ==========================================
# ผู้รับผิดชอบ: นาย ธีรภัทร พิกุลศรี
# ==========================================

@officer_bp.route('/verify', methods=['GET', 'POST'])
def verify_application():
    """ตรวจสอบเอกสารการสมัครและจัดการสถานะ (Application Verification & Status Update)"""
    return "Officer: Application Verification"

# ==========================================
# ระบบตรวจสอบใบสมัคร (Application Verification)
# ==========================================

@officer_bp.route('/')
def home():
    """หน้าแรกของระบบเจ้าหน้าที่ (Officer Dashboard)"""
    return redirect(url_for('officer.applications'))

@officer_bp.route('/applications')
def applications():
    """แสดงรายชื่อใบสมัครทั้งหมด (List all applications)"""
    status_filter = request.args.get('status')
    allowed_statuses = {'pending', 'reviewing', 'interview', 'approved'}
    if status_filter not in allowed_statuses:
        status_filter = None

    # ดึงข้อมูลใบสมัครทั้งหมด (ตามตัวกรอง)
    applications_query = Application.query
    if status_filter:
        applications_query = applications_query.filter_by(status=status_filter)
    all_applications = applications_query.all()
    
    # ดึงรายชื่อทุนทั้งหมด
    scholarships = Scholarship.query.all()
    
    # นับจำนวนตามสถานะ
    pending_count = Application.query.filter_by(status='pending').count()
    approved_count = Application.query.filter_by(status='approved').count()
    interview_count = Application.query.filter_by(status='interview').count()
    total_count = Application.query.count()
    
    # Pagination
    page = 1
    per_page = 10
    total_pages = (len(all_applications) + per_page - 1) // per_page
    start_index = (page - 1) * per_page + 1 if all_applications else 0
    end_index = min(page * per_page, len(all_applications)) if all_applications else 0
    
    return render_template('officer/applications.html', 
                         applications=all_applications,
                         scholarships=scholarships,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         interview_count=interview_count,
                         total_count=total_count,
                         page=page,
                         per_page=per_page,
                         total_pages=total_pages,
                         start_index=start_index,
                         end_index=end_index,
                         selected_status=status_filter)

@officer_bp.route('/application/<int:application_id>')
def view_application(application_id):
    """แสดงรายละเอียดใบสมัคร (View application details)"""
    application = Application.query.get_or_404(application_id)
    return render_template('officer/application-detail.html', application=application)

@officer_bp.route('/application/<int:application_id>/decision', methods=['POST'])
def decide_application(application_id):
    """อนุมัติ/ปฏิเสธใบสมัครหลังตรวจเอกสารครบ"""
    application = Application.query.get_or_404(application_id)
    decision = request.form.get('decision')
    if decision == 'interview':
        application.status = 'interview'
        db.session.commit()
        flash('ทำการยืนยันนัดสัมภาษณ์เรียบร้อยแล้ว', 'success')
    elif decision == 'pending':
        application.status = 'pending'
        db.session.commit()
        flash('ทำการยืนยันปฏิเสธใบสมัครเรียบร้อยแล้ว', 'success')
    return redirect(url_for('officer.applications'))

@officer_bp.route('/application/<int:application_id>/status/next')
def advance_status(application_id):
    """เปลี่ยนสถานะไปขั้นถัดไปแบบคลิกครั้งเดียว"""
    application = Application.query.get_or_404(application_id)
    next_status_map = {
        'pending': 'reviewing',
        'reviewing': 'interview',
        'interview': 'approved',
        'approved': 'pending',
    }
    next_status = next_status_map.get(application.status)
    if next_status:
        application.status = next_status
        db.session.commit()
    return redirect(url_for('officer.applications'))

@officer_bp.route('/audit-log')
def audit_log():
    """ระบบบันทึกประวัติการทำงาน (Audit Log)"""
    return "Officer: Audit Log System"


# ==========================================
# ผู้รับผิดชอบ: นาย อติวิชญ์ สีหนันท์
# ==========================================

@officer_bp.route('/notify', methods=['POST'])
def auto_notify():
    """ระบบแจ้งเตือนผลอัตโนมัติ (Automatic Result Notification)"""
    return "Officer: Automatic Result Notification Triggered"

@officer_bp.route('/announcement', methods=['GET', 'POST'])
def final_announcement():
    """จัดการประกาศผลรอบสุดท้าย (Final Announcement)"""
    return "Officer: Final Announcement Management"