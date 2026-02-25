from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Application, Scholarship

# สร้าง Blueprint สำหรับ Officer
officer_bp = Blueprint('officer', __name__)

# ==========================================
# ผู้รับผิดชอบ: นาย ยศสรัล ถิระบุตร (Officer ส่วนเดิม)
# ==========================================

@officer_bp.route('/login', methods=['GET', 'POST'])
def login():
    return "Officer: Login Page"

@officer_bp.route('/scholarships/<int:id>/applications')
def view_applications_by_scholarship(id):
    applications = Application.query.filter_by(scholarship_id=id).all()
    return render_template('officer/applications.html', applications=applications)

@officer_bp.route('/scholarships/add', methods=['GET', 'POST'])
def add_scholarship():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = request.form.get('amount')
        if not name or not amount:
            flash('กรุณากรอกข้อมูลให้ครบ', 'danger')
            return redirect(url_for('officer.add_scholarship'))
        new_scholarship = Scholarship(name=name, amount=float(amount))
        db.session.add(new_scholarship)
        db.session.commit()
        flash('เพิ่มทุนสำเร็จ', 'success')
        return redirect(url_for('officer.list_scholarships'))
    return render_template('officer/add_scholarship.html')

@officer_bp.route('/scholarships')
def list_scholarships():
    scholarships = Scholarship.query.all()
    return render_template('officer/scholarships.html', scholarships=scholarships)

@officer_bp.route('/scholarships/<int:id>/edit', methods=['GET', 'POST'])
def edit_scholarship(id):
    scholarship = Scholarship.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name')
        amount = request.form.get('amount')
        if not name or not amount:
            flash('กรุณากรอกข้อมูลให้ครบ', 'danger')
            return redirect(url_for('officer.edit_scholarship', id=id))
        scholarship.name = name
        scholarship.amount = float(amount)
        db.session.commit()
        flash('แก้ไขทุนสำเร็จ', 'success')
        return redirect(url_for('officer.list_scholarships'))
    return render_template('officer/edit_scholarship.html', scholarship=scholarship)

@officer_bp.route('/scholarships/<int:id>/delete', methods=['POST'])
def delete_scholarship(id):
    scholarship = Scholarship.query.get_or_404(id)
    db.session.delete(scholarship)
    db.session.commit()
    flash('ลบทุนสำเร็จ', 'success')
    return redirect(url_for('officer.list_scholarships'))

# ==========================================
# ผู้รับผิดชอบ: นาย ธีรภัทร พิกุลศรี (Officer ส่วนเดิม)
# ==========================================

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
    return render_template('officer/application-detail.html', application=application)

@officer_bp.route('/application/<int:application_id>/decision', methods=['POST'])
def decide_application(application_id):
    application = Application.query.get_or_404(application_id)
    decision = request.form.get('decision')
    if decision == 'interview':
        application.status = 'interview'
        application.reviewing_by = None
        application.reviewing_at = None
        db.session.commit()
        flash('ทำการยืนยันนัดสัมภาษณ์เรียบร้อยแล้ว', 'success')
    elif decision == 'needs_edit':
        application.status = 'needs_edit'
        application.reviewing_by = None
        application.reviewing_at = None
        db.session.commit()
        flash('ส่งกลับให้แก้ไขเอกสารเรียบร้อยแล้ว', 'success')
    return redirect(url_for('officer.applications'))

@officer_bp.route('/audit-log')
def audit_log():
    """หน้าบันทึกการทำงาน (Audit Log) ของเจ้าหน้าที่"""
    return render_template('officer/audit_log.html')

# ==========================================
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
        s.passed_docs = Application.query.filter_by(scholarship_id=s.id, status='interview').count()
    return render_template('director/scoring.html', scholarships=scholarships)

@director_bp.route('/scholarship/<int:scholarship_id>/students')
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
def audit_log():
    """หน้าบันทึกการทำงาน LOG ของกรรมการ"""
    return "Director: Audit Log System"