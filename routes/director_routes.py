from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Student, db, Scholarship, Criterion, Application, AuditLog, DirectorAuditLog  # noqa: F401

director_bp = Blueprint("director", __name__)

@director_bp.before_request
def require_director_login():
    """ตรวจสอบการล็อกอินก่อนเข้าถึงทุก Route ของ Director (ยกเว้นหน้า login)"""     
    if request.endpoint and request.endpoint != 'director.login':
        if "user_id" not in session or session.get("role") != "director":
            flash("กรุณาเข้าสู่ระบบในฐานะกรรมการ", "error")
            return redirect(url_for("login")) # Assuming login is the global login defined in app.py

# ==========================================
# 1. หน้าแสดงรายการทุนทั้งหมดdd
# ==========================================
@director_bp.route("/")
def home():
    from datetime import datetime

    # --- สถิติจริงจาก DB ---
    total_apps     = Application.query.count()
    pending_count  = Application.query.filter(
        Application.status.in_(["pending", "รอการตรวจสอบ", "รอตรวจสอบ"])
    ).count()
    reviewed_count = Application.query.filter(
        Application.status.in_(["interview", "approved", "Selected", "Reserved", "rejected", "อนุมัติ"])
    ).count()
    progress_pct   = round((reviewed_count / total_apps * 100) if total_apps > 0 else 0)

    # --- ทุนล่าสุด 5 รายการ ใช้เป็น "ประกาศ" (เฉพาะที่เปิดอยู่) ---
    all_open = [s for s in Scholarship.query.filter_by(status='open').all() if s.is_open()]
    recent_scholarships = sorted(all_open, key=lambda x: x.id, reverse=True)[:5]

    today = datetime.now()

    return render_template(
        "director/homepage.html",
        pending_count=pending_count,
        reviewed_count=reviewed_count,
        progress_pct=progress_pct,
        recent_scholarships=recent_scholarships,
        today=today,
    )


# รับผิดชอบโดย: นาย ทรงเดช จำปาเทศ
@director_bp.route("/scoring")
def scoring():
    # กรองเฉพาะทุนที่ยังเปิดอยู่
    scholarships = [s for s in Scholarship.query.filter_by(status='open').all() if s.is_open()]
    scholarship_list = []
    for sch in scholarships:
        total_applicants = Application.query.filter_by(scholarship_id=sch.id).count()
        # ผ่านเอกสาร = เจ้าหน้าที่อนุมัติสัมภาษณ์ (interview) หรือกรรมการอนุมัติ (approved/อนุมัติ)
        passed_docs = Application.query.filter(
            Application.scholarship_id == sch.id,
            Application.status.in_(['interview', 'approved', 'อนุมัติ'])
        ).count()

        scholarship_list.append({
            "id": sch.id,
            "name": sch.name,
            "total_applicants": total_applicants,
            "passed_docs": passed_docs,
        })
    return render_template("director/scoring.html", scholarships=scholarship_list)

# ==========================================
# 2. หน้าแสดงรายชื่อนักศึกษา (แก้ไขการ Join ข้อมูล)
# ==========================================
# รับผิดชอบโดย: นาย กฤชณัท ศิริรังสรรค์กุล
@director_bp.route("/scoring/<scholarship_id>")
def scholarship_students(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)

    # ดึงเฉพาะคนที่เจ้าหน้าที่อนุมัติสัมภาษณ์ (interview) หรือกรรมการอนุมัติ (approved) + Join Student เพื่อเอาค่า GPA
    query_results = (
        db.session.query(Application, Student)
        .join(Student, Application.student_id == Student.student_id)
        .filter(
            Application.scholarship_id == scholarship_id,
            Application.status.in_(['interview', 'approved'])
        )
        .all()
    )

    formatted_candidates = []
    for app, stu in query_results:
        # คำนวณคะแนนอัตโนมัติเพื่อให้ข้อมูลล่าสุดเสมอ
        app.calculate_automatic_score()
        
        formatted_candidates.append({
            "id": app.id,
            "student_id": stu.student_id,
            "student_name": stu.name or app.student_name,
            "gpa": stu.gpax,
            "is_scored": app.is_scored,
            "total_score": app.total_score,
            "status": app.status,
        })
    db.session.commit()

    return render_template(
        "director/scoring_students.html",
        scholarship_id=scholarship_id,
        scholarship_name=sch.name,
        candidates=formatted_candidates,
    )

# ==========================================
# 3. หน้าให้คะแนน (แก้ไข ID เป็น String)
# ==========================================
@director_bp.route("/score_candidate/<string:app_id>", methods=["GET", "POST"])
def give_score(app_id):
    from models import Evaluation  # Ensure Evaluation is imported
    application = Application.query.get_or_404(app_id)

    if request.method == "POST":
        score_financial = int(request.form.get("score_financial", 0))
        score_interview = int(request.form.get("score_interview", 0))
        score_volunteer = int(request.form.get("score_volunteer", 0))
        
        # --- เริ่มระบบคะแนนลับ (นับจากเหตุผล) ---
        import json
        reason_text = application.notes or ""
        if application.form_data:
            try:
                fd = json.loads(application.form_data)
                reason_text = fd.get('reason', reason_text)
            except Exception:
                pass
        
        hidden_score = min(10, len(reason_text.strip()) // 20) if reason_text else 0
        # ------------------------------------
        
        total = score_financial + score_interview + score_volunteer + hidden_score

        # Create or update evaluation
        eval_record = Evaluation.query.filter_by(application_id=app_id).first()
        if not eval_record:
            eval_record = Evaluation(
                application_id=app_id,
                committee_id=session.get('user_id', 'COM-001'), # Mocking committee ID if missing
                score_financial=score_financial,
                score_interview=score_interview,
                score_volunteer=score_volunteer
            )
            db.session.add(eval_record)
        else:
            eval_record.score_financial = score_financial
            eval_record.score_interview = score_interview
            eval_record.score_volunteer = score_volunteer

        application.total_score = total
        application.is_scored = True
        
        if request.form.get("approve_scholarship") == "1":
            if total < 50:
                flash(f"ไม่สามารถอนุมัติได้: คะแนนรวม {total} น้อยกว่าเกณฑ์ขั้นต่ำ 50 คะแนน", "error")
                # ยังคงบันทึกคะแนนไว้แต่ไม่เปลี่ยนสถานะเป็น approved
            else:
                application.status = "approved"

        log = DirectorAuditLog(
            user_name="กรรมการ (Admin)",
            action="SCORING",
            details=f"ให้คะแนนนักศึกษา {application.student_name} รหัส {application.student_id} ทุน {application.scholarship.name} ความจำเป็น={score_financial} สัมภาษณ์={score_interview} จิตอาสา={score_volunteer} (คะแนนพิเศษจากเหตุผล={hidden_score}) รวม={total}",
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()

        flash(f"บันทึกคะแนนของ {application.student_name} เรียบร้อยแล้ว (รวม {total} คะแนน)", "success")
        return redirect(url_for("director.scholarship_students", scholarship_id=application.scholarship_id))

    return render_template("director/give_score.html", student=application)

# ==========================================
# 4. อนุมัติได้รับทุน (ตั้ง status=approved)
# ==========================================
@director_bp.route("/approve/<string:app_id>", methods=["POST"])
def approve_scholarship(app_id):
    application = Application.query.get_or_404(app_id)
    if application.is_scored and application.status == "interview":
        application.status = "approved"
        db.session.commit()
    return redirect(
        url_for("director.scholarship_students", scholarship_id=application.scholarship_id)
    )

@director_bp.route("/quick_approve/<string:app_id>", methods=["POST"])
def quick_approve(app_id):
    """อนุมัติทันทีจากหน้ารายการโดยใช้คะแนนอัตโนมัติ (ผู้นำทางอำนาจกรรมการ)"""
    application = Application.query.get_or_404(app_id)
    
    # 1. คำนวณคะแนนอัตโนมัติ (ถ้ายังไม่มีการให้คะแนน)
    score = application.calculate_automatic_score()
    
    # 2. ปรับสถานะเป็นอนุมัติ (กรรมการสามารถอนุมัติได้ทันทีโดยไม่ติดเกณฑ์ 50 คะแนน)
    application.status = "approved"
    application.is_scored = True
    
    # 4. บันทึก Log
    log = DirectorAuditLog(
        user_name=session.get('user_id', 'Director'),
        action="QUICK_APPROVE",
        details=f"อนุมัติรวดเร็ว (Quick Approve) สำหรับ {application.student_name} ({application.student_id}) คะแนน={score}",
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"อนุมัติทุนให้ {application.student_name} เรียบร้อยแล้ว (คะแนน {score})", "success")
    
    # กลับไปยังหน้าเดิม (เพื่อความสะดวก ถ้ากดจากหน้าดูรายละเอียดก็กลับไปหน้าเดิม)
    # ถ้ามาจากหน้า scoring_students ก็กลับไปหน้านั้น
    return redirect(request.referrer or url_for("director.scholarship_students", scholarship_id=application.scholarship_id))

@director_bp.route("/reject/<string:app_id>", methods=["POST"])
def reject_application(app_id):
    """ปฏิเสธการให้ทุน"""
    application = Application.query.get_or_404(app_id)
    application.status = "rejected"
    
    log = DirectorAuditLog(
        user_name=session.get('user_id', 'Director'),
        action="REJECT_APPLICATION",
        details=f"ปฏิเสธใบสมัครของ {application.student_name} ({application.student_id})",
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"ปฏิเสธใบสมัครของ {application.student_name} เรียบร้อยแล้ว", "info")
    return redirect(url_for("director.scholarship_students", scholarship_id=application.scholarship_id))


# ==========================================
# 5. หน้าดูรายละเอียดนักศึกษา
# ==========================================
# รับผิดชอบโดย: นาย กฤชณัท ศิริรังสรรค์กุล
@director_bp.route("/candidate/<string:app_id>")
def candidate_detail(app_id):
    import os
    application = Application.query.get_or_404(app_id)
    student = Student.query.filter_by(student_id=application.student_id).first()

    # ค้นหารูปนักศึกษา (ดึงจากโปรไฟล์นักศึกษาใน static/images/students ก่อน)
    photo_url = None
    all_app_files = []
    if student:
        from flask import current_app
        # 1. ลองดึงจากโฟลเดอร์ profile ของนักศึกษาโดยตรง
        profile_pic_path = os.path.join(current_app.static_folder, 'images', 'students', f"{student.student_id}.jpg")
        if os.path.exists(profile_pic_path):
            photo_url = f"images/students/{student.student_id}.jpg"
        else:
            # 2. ถ้าไม่มี ค่อยไปหาในโฟลเดอร์เอกสารที่อัปโหลดตอนสมัคร
            upload_dir = os.path.join(current_app.static_folder, 'uploads', str(student.student_id))
            image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            if os.path.isdir(upload_dir):
                files = os.listdir(upload_dir)
                app_images = [f for f in files if f.startswith(f"app_{app_id}") and os.path.splitext(f)[1].lower() in image_exts]
                all_images = [f for f in files if os.path.splitext(f)[1].lower() in image_exts]
                chosen = (app_images or all_images)
                if chosen:
                    photo_url = f"uploads/{student.student_id}/{chosen[0]}"
            
        # 3. ดึงไฟล์ทั้งหมดที่อัปโหลดพร้อมใบสมัครนี้
        upload_dir = os.path.join(current_app.static_folder, 'uploads', str(student.student_id))
        if os.path.isdir(upload_dir):
            all_app_files = [f for f in os.listdir(upload_dir) if f.startswith(f"app_{app_id}")]

    # แปลง JSON form_data เป็น dict
    form_info = {}
    if application.form_data:
        try:
            import json
            form_info = json.loads(application.form_data)
        except Exception:
            form_info = {}

    # คำนวณคะแนนและวิเคราะห์แบบอัจฉริยะเพื่อให้ข้อมูลล่าสุด
    application.calculate_automatic_score()
    smart_analysis = application.generate_smart_analysis()
    db.session.commit()

    return render_template("director/candidate_detail.html", 
                           student=application, 
                           photo_url=photo_url, 
                           student_obj=student,
                           form_info=form_info,
                           smart_analysis=smart_analysis,
                           documents=all_app_files)


# ==========================================
# 5. การจัดอันดับ (Ranking)
# ==========================================
# รับผิดชอบโดย: นาย ทรงเดช จำปาเทศ
@director_bp.route("/ranking/<scholarship_id>")
def scholarship_ranking(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    # Only show candidates who are approved/selected/reserved AND scored >= 50
    ranked_candidates = (
        Application.query.filter(
            Application.scholarship_id == scholarship_id,
            Application.is_scored == True,
            Application.total_score >= 50,
            Application.status.in_(['approved', 'Selected', 'Reserved', 'completed', 'อนุมัติ'])
        )
        .all()
    )

    # คำนวณคะแนนใหม่อัตโนมัติสำหรับทุกคน (เพื่อให้ได้ค่าล่าสุด)
    for app in ranked_candidates:
        app.calculate_automatic_score()
    db.session.commit()

    # ดึงข้อมูลอีกครั้งแบบเรียงลำดับ
    ranked_candidates = (
        Application.query.filter(
            Application.scholarship_id == scholarship_id,
            Application.is_scored == True,
            Application.total_score >= 50,
            Application.status.in_(['approved', 'Selected', 'Reserved', 'completed', 'อนุมัติ'])
        )
        .order_by(Application.total_score.desc())
        .all()
    )

    stats = {
        "total_ranked": len(ranked_candidates),
        "max_score": ranked_candidates[0].total_score if ranked_candidates else 0,
        "quota": sch.number_of_scholarships or 0,
    }
    return render_template("director/ranking.html", scholarship=sch, candidates=ranked_candidates, stats=stats)

@director_bp.route("/confirm_selection/<string:scholarship_id>", methods=["POST"])
def confirm_selection(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    candidates = (
        Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)
        .order_by(Application.total_score.desc())
        .all()
    )

    quota = sch.number_of_scholarships or 0
    selected_count = 0
    for app in candidates:
        if app.total_score >= 50 and selected_count < quota:
            app.status = "Selected"
            selected_count += 1
        else:
            app.status = "Reserved"

    # Set scholarship status to announce so it's finalized
    sch.status = 'announce'
    if not sch.announcement_date:
        from datetime import datetime
        sch.announcement_date = datetime.now()

    log = DirectorAuditLog(
        user_name="กรรมการ (Admin)",
        action="CONFIRM_SELECTION",
        details=f"ยืนยันและประกาศผลการคัดเลือกทุน {sch.name} (คัดเลือก {selected_count} รายจากโควตา {quota})",
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()

    flash(f"ยืนยันผลการคัดเลือกทุน {sch.name} เรียบร้อยแล้ว", "success")
    return redirect(url_for("director.scholarship_ranking", scholarship_id=scholarship_id))

@director_bp.route("/ranking-selection")
def ranking_selection():
    # กรองเฉพาะทุนที่เปิดอยู่
    scholarships = [s for s in Scholarship.query.filter_by(status='open').all() if s.is_open()]
    return render_template("director/ranking_selection.html", scholarships=scholarships)

@director_bp.route("/audit_log")
def audit_log():
    all_logs = DirectorAuditLog.query.order_by(DirectorAuditLog.timestamp.desc()).all()
    return render_template("director/audit_log.html", logs=all_logs)


@director_bp.route("/profile")
def profile():
    """หน้าประวัติส่วนตัวกรรมการ"""
    from models import Director
    director = Director.query.filter_by(username=session.get('user_id')).first_or_404()
    return render_template("director/profile.html", director=director)
