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

@officer_bp.route('/verify', methods=['GET'])
def verify_application():
    """หน้ารายการใบสมัครสำหรับตรวจสอบ"""
    # TODO: ดึงข้อมูลใบสมัครจริงจากฐานข้อมูลมาทีหลัง
    applications = []  # ตอนนี้ใส่ list ว่างไว้ก่อน หรือ mock data ก็ได้

    return render_template('officer/applications.html', applications=applications)

@officer_bp.route('/verify/<string:application_id>', methods=['GET', 'POST'])
def verify_application_detail(application_id):
    """หน้าดูรายละเอียดและบันทึกผลการตรวจของใบสมัครหนึ่งรายการ"""

    # TODO: ดึงใบสมัครจริงจากฐานข้อมูล
    application = None  # หรือ mock data ชั่วคราว

    if request.method == 'POST':
        # รับค่าจากฟอร์ม ที่คุณกำหนดใน application-detail.html
        decision = request.form.get('decision')      # เช่น approve / reject
        comment = request.form.get('comment')        # ความเห็นเจ้าหน้าที่

        # TODO: บันทึกลงฐานข้อมูล + เขียน audit log
        # ...

        # เสร็จแล้ว redirect กลับหน้า list
        from flask import redirect, url_for
        return redirect(url_for('officer.verify_application'))

    return render_template('officer/application-detail.html', application=application)
    
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