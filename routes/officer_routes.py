from flask import Blueprint, render_template, request

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