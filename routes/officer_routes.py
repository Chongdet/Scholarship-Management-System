import os
import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from models import db, Application, Scholarship, AuditLog, Officer, Student
from sqlalchemy import or_

# สร้าง Blueprint สำหรับ Officer
officer_bp = Blueprint('officer', __name__)

# ตั้งค่าการอัปโหลดไฟล์
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """บันทึกไฟล์ที่อัปโหลดและคืนชื่อไฟล์ที่บันทึก"""
    if file and allowed_file(file.filename):
        # สร้างชื่อไฟล์ที่ปลอดภัย
        filename = secure_filename(file.filename)
        # เพิ่ม timestamp เพื่อหลีกเลี่ยงการทับซ้อน
        random_string = secrets.token_hex(4)
        filename = f"{random_string}_{filename}"
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return filename
    return None

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
        print(f"\n=== ADD SCHOLARSHIP POST REQUEST ===")
        print(f"Form data received: {request.form}")
        print(f"All keys: {list(request.form.keys())}")
        # 1. ดึงค่าจาก HTML (ใช้ชื่อเดียวกับ attribute 'name' ใน <input>)
        s_id = (request.form.get('scholarship_id') or '').strip()
        s_name = (request.form.get('scholarship_name') or '').strip()
        print(f"scholarship_id: '{s_id}'")
        print(f"scholarship_name: '{s_name}'")

        # Server-side validation: require id and name
        if not s_id:
            print("ERROR: scholarship_id is empty")
            flash('กรุณากรอก รหัสทุนการศึกษา', 'danger')
            return render_template('officer/add_scholarship.html')
        if not s_name:
            print("ERROR: scholarship_name is empty")
            flash('กรุณากรอก ชื่อทุนการศึกษา', 'danger')
            return render_template('officer/add_scholarship.html')

        # Prevent duplicate IDs
        if Scholarship.query.filter_by(id=s_id).first():
            print(f"ERROR: scholarship_id '{s_id}' already exists")
            flash(f'รหัสทุน {s_id} มีอยู่ในระบบแล้ว กรุณาใช้รหัสอื่น', 'danger')
            return render_template('officer/add_scholarship.html')
        
        # 2. แปลงข้อมูล
        try:
            amt = float(request.form.get('amount')) if request.form.get('amount') else 0.0
            min_g = float(request.form.get('min_gpax')) if request.form.get('min_gpax') else 0.0
            print(f"amount: {amt}, min_gpax: {min_g}")
            
            # สำคัญ: Model เป็น db.Date ต้องใช้ .date()
            sd = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
            ed = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
            print(f"start_date: {sd}, end_date: {ed}")
            
            # 3. สร้าง Object (ต้องใช้ชื่อ id และ name ตาม class Scholarship)
            # Normalize status to lowercase to match model conventions
            status_val = (request.form.get('status') or 'open').lower()
            print(f"status: '{status_val}'")
            
            # จัดการการอัปโหลดไฟล์รูปภาพ
            image_filename = None
            if 'scholarship_image' in request.files:
                file = request.files['scholarship_image']
                if file and file.filename:
                    image_filename = save_uploaded_file(file)
            
            # อ่านค่าฟิลด์ใหม่
            num_scholarships = request.form.get('number_of_scholarships')
            num_scholarships = int(num_scholarships) if num_scholarships else 1
            
            new_scholarship = Scholarship(
                id=s_id,             # ใน Model คือ id
                name=s_name,         # ใน Model คือ name
                amount=amt,
                min_gpax=min_g,
                faculty_condition=request.form.get('faculty_condition'),
                start_date=sd,
                end_date=ed,
                status=status_val,
                # ฟิลด์ใหม่
                image=image_filename,
                qualifications=request.form.get('qualifications'),
                conditions=request.form.get('conditions'),
                scholarship_type=request.form.get('scholarship_type'),
                scholarship_nature=request.form.get('scholarship_nature'),
                number_of_scholarships=num_scholarships,
                required_documents=request.form.get('required_documents')
            )

            print(f"Creating scholarship: {new_scholarship}")
            db.session.add(new_scholarship)
            db.session.commit()
            print(f"SUCCESS: Scholarship '{s_id}' created successfully")
            flash('เพิ่มทุนสำเร็จ', 'success')
            officer = session.get("user_id") if session.get("role") == "officer" else None
            if officer:
                _log_audit(officer, "add_scholarship", "เพิ่มทุน",
                           reference_id=f"SCH{new_scholarship.id}",
                           details=f"ทุน {s_name}",
                           status_after=status_val or "Open")
                db.session.commit()
            return redirect(url_for('officer.list_scholarships'))

        except Exception as e:
            db.session.rollback()
            print(f"EXCEPTION: {type(e).__name__}: {e}")
            print(f"DEBUG ERROR: {e}") # ดู Error ใน Terminal ของคุณ
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
            print("=== END ADD SCHOLARSHIP POST REQUEST ===\n")
            return render_template('officer/add_scholarship.html')

    return render_template('officer/add_scholarship.html')


@officer_bp.route('/scholarships')
def list_scholarships():
    scholarships = Scholarship.query.all()
    return render_template('officer/scholarships.html', scholarships=scholarships)


@officer_bp.route('/scholarships/<scholarship_id>/edit', methods=['GET', 'POST'])
def edit_scholarship(scholarship_id):
    # ใช้ filter_by(id=...) ให้ตรงกับ Model
    scholarship = Scholarship.query.filter_by(id=scholarship_id).first_or_404()
    
    if request.method == 'POST':
        # รับค่าจากฟอร์ม
        s_name = request.form.get('scholarship_name') or request.form.get('name')
        
        if not s_name:
            flash('กรุณากรอกชื่อทุน', 'danger')
            return redirect(url_for('officer.edit_scholarship', scholarship_id=scholarship_id))

        prev_name = scholarship.name
        prev_status = scholarship.status
        scholarship.name = s_name

        try:
            amt = request.form.get('amount')
            scholarship.amount = float(amt) if amt else 0.0
            
            gpax = request.form.get('min_gpax')
            scholarship.min_gpax = float(gpax) if gpax else 0.0
            
            sd = request.form.get('start_date')
            ed = request.form.get('end_date')
            scholarship.start_date = datetime.strptime(sd, '%Y-%m-%d').date() if sd else None
            scholarship.end_date = datetime.strptime(ed, '%Y-%m-%d').date() if ed else None
            
            scholarship.faculty_condition = request.form.get('faculty_condition')
            status_val = request.form.get('status')
            if status_val:
                scholarship.status = status_val.lower()
            
            # จัดการไฟล์รูปภาพใหม่
            if 'scholarship_image' in request.files:
                file = request.files['scholarship_image']
                if file and file.filename:
                    image_filename = save_uploaded_file(file)
                    if image_filename:
                        scholarship.image = image_filename
            
            # อัปเดตฟิลด์ใหม่
            scholarship.qualifications = request.form.get('qualifications')
            scholarship.conditions = request.form.get('conditions')
            scholarship.scholarship_type = request.form.get('scholarship_type')
            scholarship.scholarship_nature = request.form.get('scholarship_nature')
            
            num_scholarships = request.form.get('number_of_scholarships')
            if num_scholarships:
                scholarship.number_of_scholarships = int(num_scholarships)
            
            scholarship.required_documents = request.form.get('required_documents')
            
            officer = session.get("user_id") if session.get("role") == "officer" else None
            if officer:
                _log_audit(officer, "edit_scholarship", "แก้ไขทุน",
                           reference_id=f"SCH{scholarship.id}",
                           details=f"ทุน {s_name}",
                           status_after=status_val or prev_status,
                           previous_value=f"ชื่อ: {prev_name}, สถานะ: {prev_status}")
            db.session.commit()
            flash('แก้ไขข้อมูลทุนเรียบร้อยแล้ว', 'success')
            return redirect(url_for('officer.list_scholarships'))
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')

    return render_template('officer/edit_scholarship.html', scholarship=scholarship)

@officer_bp.route('/scholarships/<scholarship_id>/delete', methods=['POST'])
def delete_scholarship(scholarship_id):
    """ลบทุน (Delete scholarship)"""
    scholarship = Scholarship.query.filter_by(id=scholarship_id).first_or_404()
    sch_name = scholarship.name
    try:
        officer = session.get("user_id") if session.get("role") == "officer" else None
        if officer:
            _log_audit(officer, "delete_scholarship", "ลบทุน",
                       reference_id=f"SCH{scholarship_id}",
                       details=f"ทุน {sch_name}",
                       status_after="ลบแล้ว")
        db.session.delete(scholarship)
        db.session.commit()
        flash(f'ลบทุน {sch_name} สำเร็จแล้ว', 'success')
    except Exception as e:
        db.session.rollback()
        flash('ไม่สามารถลบทุนได้ เนื่องจากมีข้อมูลผู้สมัครเชื่อมโยงอยู่', 'danger')

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
    approved_count = Application.query.filter(
        or_(
            Application.status == 'approved', 
            Application.status == 'Selected',
            Application.status == 'ได้รับทุนการศึกษา'
        )
    ).count()
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

@officer_bp.route('/application/<string:application_id>')
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

@officer_bp.route('/application/<string:application_id>/decision', methods=['POST'])
def decide_application(application_id):
    application = Application.query.get_or_404(application_id)
    decision = request.form.get('decision')
    reject_reason = request.form.get('reject_reason', '').strip()
    date_str = request.form.get('interview_date')

    if decision == 'interview':
        prev_status = application.status
        application.status = 'interview'
        application.reviewing_by = None
        application.reviewing_at = None
        application.status_description = None
        if date_str:
            application.interview_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        application.interview_time = request.form.get('interview_time')
        application.interview_location = request.form.get('interview_location')
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
        application.status_description = reject_reason or 'กรุณาแก้ไขเอกสารให้ครบถ้วน'
        application.reject_reason = reject_reason
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