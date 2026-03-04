import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Application, Scholarship, AuditLog, Officer, Student

# สร้าง Blueprint สำหรับ Officer
officer_bp = Blueprint('officer', __name__)

# ==========================================
# ผู้รับผิดชอบ: นาย ยศสรัล ถิระบุตร (Officer ส่วนเดิม)
# ==========================================

@officer_bp.route('/login', methods=['GET', 'POST'])
def login():
    return "Officer: Login Page"

# =========================
# แสดงรายการใบสมัครของทุน
# =========================
@officer_bp.route('/scholarships/<scholarship_id>/applications')
def view_applications_by_scholarship(scholarship_id):
    # เปลี่ยนให้รับ scholarship_id เป็น String ตาม Database Schema ใหม่
    applications = Application.query.filter_by(scholarship_id=scholarship_id).all()
    return render_template('officer/applications.html', applications=applications)

@officer_bp.route('/scholarships/add', methods=['GET', 'POST'])
def add_scholarship():
    if request.method == 'POST':
        # รับค่าจากฟอร์มให้ครอบคลุมทั้ง 2 ฝั่ง
        scholarship_id = request.form.get('scholarship_id')
        scholarship_name = request.form.get('scholarship_name') or request.form.get('name') 
        amount = request.form.get('amount')
        min_gpax = request.form.get('min_gpax')
        faculty_condition = request.form.get('faculty_condition')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status')

        if not scholarship_id or not scholarship_name:
            flash('กรุณากรอกรหัสและชื่อทุนให้ครบถ้วน', 'danger')
            return redirect(url_for('officer.add_scholarship'))

        # convert types
        try:
            amt = float(amount) if amount else None
        except ValueError:
            amt = None
        try:
            min_g = float(min_gpax) if min_gpax else None
        except ValueError:
            min_g = None
            
        sd = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        ed = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

        new_scholarship = Scholarship(
            scholarship_id=scholarship_id,
            scholarship_name=scholarship_name,
            amount=amt,
            min_gpax=min_g,
            faculty_condition=faculty_condition or None,
            start_date=sd,
            end_date=ed,
            status=status or 'Open'
        )

        db.session.add(new_scholarship)
        db.session.commit()
        officer = session.get("user_id") if session.get("role") == "officer" else None
        if officer:
            _log_audit(officer, "add_scholarship", "เพิ่มทุน",
                       reference_id=f"SCH{new_scholarship.id}",
                       details=f"ทุน {scholarship_name}",
                       status_after=status or "Open")
            db.session.commit()
        flash('เพิ่มทุนสำเร็จ', 'success')
        return redirect(url_for('officer.list_scholarships'))
    return render_template('officer/add_scholarship.html')


@officer_bp.route('/scholarships')
def list_scholarships():
    scholarships = Scholarship.query.all()
    return render_template('officer/scholarships.html', scholarships=scholarships)


@officer_bp.route('/scholarships/<scholarship_id>/edit', methods=['GET', 'POST'])
def edit_scholarship(scholarship_id):
    """แก้ไขทุน (Edit scholarship)"""
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    if request.method == 'POST':
        scholarship_name = request.form.get('scholarship_name') or request.form.get('name')
        amount = request.form.get('amount')
        min_gpax = request.form.get('min_gpax')
        faculty_condition = request.form.get('faculty_condition')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status')

        if not scholarship_name:
            flash('กรุณากรอกชื่อทุน', 'danger')
            return redirect(url_for('officer.edit_scholarship', scholarship_id=scholarship_id))

        prev_name = getattr(scholarship, 'scholarship_name', None) or scholarship.name
        prev_status = getattr(scholarship, 'status', None)
        scholarship.scholarship_name = scholarship_name
        try:
            scholarship.amount = float(amount) if amount else None
        except ValueError:
            pass
        try:
            scholarship.min_gpax = float(min_gpax) if min_gpax else None
        except ValueError:
            pass
            
        scholarship.faculty_condition = faculty_condition or None
        scholarship.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        scholarship.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        scholarship.status = status or scholarship.status

        db.session.commit()
        officer = session.get("user_id") if session.get("role") == "officer" else None
        if officer:
            _log_audit(officer, "edit_scholarship", "แก้ไขทุน",
                       reference_id=f"SCH{scholarship.id}",
                       details=f"ทุน {scholarship_name}",
                       status_after=status or prev_status,
                       previous_value=f"ชื่อ: {prev_name}, สถานะ: {prev_status}")
            db.session.commit()
        flash('แก้ไขทุนสำเร็จ', 'success')
        return redirect(url_for('officer.list_scholarships'))
    return render_template('officer/edit_scholarship.html', scholarship=scholarship)

@officer_bp.route('/scholarships/<scholarship_id>/delete', methods=['POST'])
def delete_scholarship(scholarship_id):
    """ลบทุน (Delete scholarship)"""
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    sch_name = getattr(scholarship, 'scholarship_name', None) or scholarship.name
    officer = session.get("user_id") if session.get("role") == "officer" else None
    if officer:
        _log_audit(officer, "delete_scholarship", "ลบทุน",
                   reference_id=f"SCH{scholarship_id}",
                   details=f"ทุน {sch_name}",
                   status_after="ลบแล้ว")
    db.session.delete(scholarship)
    db.session.commit()
    flash('ลบทุนสำเร็จ', 'success')
    return redirect(url_for('officer.list_scholarships'))


# ==========================================
# ผู้รับผิดชอบ: นาย ธีรภัทร พิกุลศรี
# (Audit Log, Application, Application-detail)
# ==========================================

def _log_audit(officer_username: str, action: str, action_title: str,
               reference_id: str = None, details: str = None,
               status_after: str = None, previous_value: str = None):
    """บันทึก Audit Log"""
    if not officer_username:
        return
    officer = Officer.query.filter_by(username=officer_username).first()
    log = AuditLog(
        officer_username=officer_username,
        officer_label=officer.name if officer else officer_username,
        action=action,
        action_title=action_title,
        reference_id=reference_id,
        details=details,
        status_after=status_after,
        previous_value=previous_value,
    )
    db.session.add(log)


@officer_bp.route('/')
def home():
    return redirect(url_for('officer.applications'))

@officer_bp.route('/applications')
def applications():
    status_filter = request.args.get('status')
    allowed_statuses = {'pending', 'reviewing', 'needs_edit', 'interview', 'approved'}
    if status_filter not in allowed_statuses:
        status_filter = None

    applications_query = Application.query
    if status_filter:
        applications_query = applications_query.filter_by(status=status_filter)
    all_applications = applications_query.all()
    
    scholarships = Scholarship.query.all()
    pending_count = Application.query.filter_by(status='pending').count()
    approved_count = Application.query.filter_by(status='approved').count()
    interview_count = Application.query.filter_by(status='interview').count()
    needs_edit_count = Application.query.filter_by(status='needs_edit').count()
    total_count = Application.query.count()
    
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
                         needs_edit_count=needs_edit_count,
                         page=page, per_page=per_page, total_pages=total_pages,
                         start_index=start_index, end_index=end_index,
                         selected_status=status_filter)

@officer_bp.route('/application/<int:application_id>')
def view_application(application_id):
    current_officer = session.get("user_id") if session.get("role") == "officer" else None
    if not current_officer:
        flash('กรุณาเข้าสู่ระบบเจ้าหน้าที่ก่อน', 'error')
        return redirect(url_for('login'))
        
    application = Application.query.get_or_404(application_id)
    
    if application.status == 'reviewing' and application.reviewing_by and application.reviewing_by != current_officer:
        flash(f'ใบสมัครนี้กำลังตรวจสอบโดย {application.reviewing_by}', 'warning')
        return redirect(url_for('officer.applications'))

    if application.status in {'pending', 'needs_edit', 'reviewing'}:
        if application.reviewing_by != current_officer or application.status != 'reviewing':
            application.status = 'reviewing'
            application.reviewing_by = current_officer
            application.reviewing_at = datetime.utcnow()
            db.session.commit()
    
    student = Student.query.filter_by(student_id=application.student_id).first()
    return render_template('officer/application-detail.html', application=application, student=student)

@officer_bp.route('/application/<int:application_id>/decision', methods=['POST'])
def decide_application(application_id):
    application = Application.query.get_or_404(application_id)
    decision = request.form.get('decision')
    reject_reason = request.form.get('reject_reason', '').strip()
    
    if decision == 'interview':
        prev_status = application.status
        application.status = 'interview'
        application.reviewing_by = None
        application.reviewing_at = None
        application.status_description = None
        db.session.commit()
        officer = session.get("user_id") if session.get("role") == "officer" else None
        if officer:
            sch_name = application.scholarship.name if application.scholarship else "ทุน"
            _log_audit(officer, "approve_interview", "ยืนยันนัดสัมภาษณ์",
                       reference_id=f"APP{application.id}",
                       details=f"{application.student_name} - {sch_name}",
                       status_after="interview",
                       previous_value=prev_status)
            db.session.commit()

        # ส่งอีเมลแจ้งเตือนอนุมัติ/นัดสัมภาษณ์
        student = Student.query.filter_by(student_id=application.student_id).first()
        to_email = (student.email if student else None) or ""
        if student or os.getenv("EMAIL_OVERRIDE"):
            try:
                from services.email_service import send_interview_notification
                sent = send_interview_notification(
                    to_email=to_email or "test@test.com",
                    student_name=application.student_name or (student.name if student else "นักศึกษา"),
                    scholarship_name=application.scholarship.name if application.scholarship else "ทุนการศึกษา",
                )
                if sent:
                    flash("ทำการยืนยันนัดสัมภาษณ์และส่งอีเมลแจ้งเตือนเรียบร้อยแล้ว", "success")
                else:
                    flash("ทำการยืนยันนัดสัมภาษณ์เรียบร้อยแล้ว (อีเมลส่งไม่ได้)", "success")
            except Exception as e:
                flash(f"ทำการยืนยันนัดสัมภาษณ์เรียบร้อยแล้ว (ข้อผิดพลาดอีเมล: {e})", "success")
        else:
            flash("ทำการยืนยันนัดสัมภาษณ์เรียบร้อยแล้ว", "success")
    elif decision == 'needs_edit':
        prev_status = application.status
        application.status = 'needs_edit'
        application.reviewing_by = None
        application.reviewing_at = None
        application.status_description = reject_reason or 'กรุณาแก้ไขเอกสารให้ครบถ้วน'
        db.session.commit()
        officer = session.get("user_id") if session.get("role") == "officer" else None
        if officer:
            sch_name = application.scholarship.name if application.scholarship else "ทุน"
            _log_audit(officer, "reject_needs_edit", "ส่งกลับให้แก้ไข",
                       reference_id=f"APP{application.id}",
                       details=f"{application.student_name} - {sch_name}",
                       status_after="needs_edit",
                       previous_value=prev_status)
            db.session.commit()

        # ส่งอีเมลแจ้งเตือนไปที่อีเมลนักศึกษาที่ผูกไว้ (หรือ EMAIL_OVERRIDE ถ้าตั้งค่า)
        student = Student.query.filter_by(student_id=application.student_id).first()
        to_email = (student.email if student else None) or ""
        # ถ้ามี EMAIL_OVERRIDE ให้ลองส่งได้แม้นักศึกษาไม่มีอีเมล
        if student or os.getenv("EMAIL_OVERRIDE"):
            try:
                from services.email_service import send_reject_notification
                sent = send_reject_notification(
                    to_email=to_email or "test@test.com",
                    student_name=application.student_name or (student.name if student else "นักศึกษา"),
                    scholarship_name=application.scholarship.name if application.scholarship else "ทุนการศึกษา",
                    reject_reason=application.status_description
                )
                if sent:
                    flash("ส่งกลับให้แก้ไขเอกสารและส่งอีเมลแจ้งเตือนเรียบร้อยแล้ว", "success")
                else:
                    flash("ส่งกลับให้แก้ไขเอกสารเรียบร้อยแล้ว (อีเมลส่งไม่ได้ - ดูเทอร์มินัลหรือตั้ง DEBUG_EMAIL=1)", "warning")
            except Exception as e:
                flash(f"ส่งกลับให้แก้ไขเอกสารเรียบร้อยแล้ว (ข้อผิดพลาด: {e})", "warning")
        else:
            flash("ส่งกลับให้แก้ไขเอกสารเรียบร้อยแล้ว (นักศึกษาไม่มีอีเมลในระบบ)", "success")
        
    return redirect(url_for('officer.applications'))

@officer_bp.route('/audit-log')
def audit_log():
    """หน้าบันทึกการทำงาน (Audit Log) ของเจ้าหน้าที่"""
    staff_filter = request.args.get('staff', '')
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if staff_filter:
        query = query.filter(
            db.or_(
                AuditLog.officer_username == staff_filter,
                AuditLog.officer_label == staff_filter
            )
        )
    logs = query.all()
    
    for log in logs:
        officer = Officer.query.filter_by(username=log.officer_username).first()
        log.officer_id = officer.id if officer else None
        log.officer_name = officer.name if (officer and officer.name) else (log.officer_label or log.officer_username)
        
    all_logs = AuditLog.query.all()
    staff_set = set()
    for log in all_logs:
        staff_set.add(log.officer_label or log.officer_username)
    staff_list = sorted(staff_set) if staff_set else []
    
    return render_template('officer/audit_log.html', logs=logs, staff_list=staff_list, total_count=len(logs), selected_staff=staff_filter)


# ==========================================
# ผู้รับผิดชอบ: นาย อติวิชญ์ สีหนันท์ (ประกาศทุน / ผู้ได้รับทุน)
# ==========================================

@officer_bp.route('/announcement')
def final_announcement():
    """หน้าประกาศผลทุน"""
    scholarships = Scholarship.query.all()
    return render_template('officer/announcement.html', scholarships=scholarships)

@officer_bp.route('/scholarship/<scholarship_id>/recipients', methods=['GET', 'POST'])
def scholarship_recipients(scholarship_id):
    """หน้าผู้ได้รับทุน - ดู/กำหนดวันที่ประกาศ"""
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    if request.method == 'POST':
        date_str = request.form.get('announcement_date')
        if date_str:
            announcement_date = datetime.strptime(date_str, '%Y-%m-%d')
            scholarship.announcement_date = announcement_date
            db.session.commit()

            # ส่งอีเมลแจ้งเตือนให้นักศึกษาทุกคนที่สมัครทุนนี้
            from services.email_service import send_announcement_notification

            applications = Application.query.filter_by(scholarship_id=scholarship.id).all()
            date_display = announcement_date.strftime('%d/%m/%Y')
            sent_count = 0
            for app in applications:
                student = Student.query.filter_by(student_id=app.student_id).first()
                to_email = student.email if student else None
                if to_email and "@" in str(to_email):
                    if send_announcement_notification(
                        to_email=to_email,
                        student_name=app.student_name or (student.name if student else "นักศึกษา"),
                        scholarship_name=scholarship.name,
                        announcement_date=date_display,
                    ):
                        sent_count += 1

            officer = session.get("user_id") if session.get("role") == "officer" else None
            if officer:
                _log_audit(officer, "set_announcement", "กำหนดวันประกาศผลทุน",
                           reference_id=f"SCH{scholarship.id}",
                           details=f"{scholarship.name} - วันที่ {date_display}",
                           status_after=date_display)
                db.session.commit()

            if sent_count > 0:
                flash(f"บันทึกวันที่ประกาศเรียบร้อย และส่งอีเมลแจ้งเตือนไปแล้ว {sent_count} คน", "success")
            else:
                flash("บันทึกวันที่ประกาศเรียบร้อย", "success")
        else:
            scholarship.announcement_date = None
            db.session.commit()
            flash("บันทึกวันที่ประกาศเรียบร้อย", "success")
        return redirect(url_for('officer.final_announcement'))
        
    applications = Application.query.filter_by(scholarship_id=scholarship_id, status='approved').all()
    if not applications:
        applications = Application.query.filter_by(scholarship_id=scholarship_id, status='interview').all()
    return render_template('officer/recipients.html', scholarship=scholarship, applications=applications)


# ==========================================
# (หากใน app.py โหลด Director Blueprint จากที่อื่นแล้ว คุณสามารถลบส่วนด้านล่างนี้ทิ้งได้)
# เพิ่มส่วนของกรรมการ (Director) เพื่อให้ Link ใน HTML ทำงานได้
# ==========================================
director_bp = Blueprint('director', __name__)

@director_bp.route('/home')
def home():
    """หน้า Dashboard ของกรรมการ"""
    return render_template('director/dashboard.html')

@director_bp.route('/scoring')
def scoring():
    """หน้าพิจารณาทุน (หน้าที่มีปัญหา Link หาย)"""
    scholarships = Scholarship.query.all()
    # เพิ่ม Logic เพื่อนับจำนวนผู้สมัครในแต่ละสถานะให้ Template
    for s in scholarships:
        s.total_applicants = len(s.applications)
        s.passed_docs = Application.query.filter_by(scholarship_id=s.scholarship_id, status='interview').count()
    return render_template('director/scoring.html', scholarships=scholarships)

@director_bp.route('/scholarship/<scholarship_id>/students')
def scholarship_students(scholarship_id):
    """หน้าแสดงรายชื่อนักศึกษาในทุนนั้นๆ สำหรับกรรมการ"""
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    # ดึงเฉพาะคนที่ผ่านเอกสาร (interview) มาให้กรรมการให้คะแนน
    applications = Application.query.filter_by(scholarship_id=scholarship_id, status='interview').all()
    return render_template('director/scholarship_students.html', scholarship=scholarship, applications=applications)

@director_bp.route('/ranking')
def ranking():
    """หน้าจัดอันดับและยืนยันผล"""
    return render_template('director/ranking.html')

@director_bp.route('/audit_log')
def director_audit_log():
    """หน้าบันทึกการทำงาน LOG ของกรรมการ"""
    return "Director: Audit Log System"