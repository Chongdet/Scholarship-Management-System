from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import Student, db, Scholarship, Criterion, Application, AuditLog
from routes.officer_routes import director_audit_log

director_bp = Blueprint("director", __name__)

# ==========================================
# 1. หน้าแสดงรายการทุนทั้งหมด
# ==========================================
@director_bp.route("/")
def home():
    return render_template("director/homepage.html")

@director_bp.route("/scoring")
def scoring():
    scholarships = Scholarship.query.all()
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
@director_bp.route("/scoring/<string:scholarship_id>")
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
        formatted_candidates.append({
            "id": app.id,
            "student_id": stu.student_id,
            "student_name": stu.name or app.student_name,
            "gpa": stu.gpax,
            "is_scored": app.is_scored,
            "total_score": app.total_score,
            "status": app.status,
        })

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
    application = Application.query.get_or_404(app_id)
    criteria = Criterion.query.filter_by(
        scholarship_id=application.scholarship_id
    ).all()

    if request.method == "POST":
        total = 0
        for c in criteria:
            score_val = request.form.get(f"score_{c.id}", "0")
            try:
                total += int(score_val)
            except ValueError:
                total += 0

        application.total_score = total
        application.is_scored = True
        if request.form.get("approve_scholarship") == "1":
            application.status = "approved"

        log = director_audit_log(
            user_name="กรรมการ (Admin)",
            action="SCORING",
            details=f"ให้คะแนนนักศึกษา {application.student_name} รหัส {application.student_id} ทุน {application.scholarship.name} คะแนนรวม {total}",
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()

        flash(f"บันทึกคะแนนของ {application.student_name} เรียบร้อยแล้ว", "success")
        return redirect(url_for("director.scholarship_students", scholarship_id=application.scholarship_id))

    return render_template("director/give_score.html", student=application, criteria=criteria)

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


# ==========================================
# 5. หน้าดูรายละเอียดนักศึกษา
# ==========================================
@director_bp.route("/candidate/<string:app_id>")
def candidate_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("director/candidate_detail.html", student=application)

# ==========================================
# 5. การจัดอันดับ (Ranking)
# ==========================================
@director_bp.route("/ranking/<string:scholarship_id>")
def scholarship_ranking(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    ranked_candidates = (
        Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)
        .order_by(Application.total_score.desc())
        .all()
    )

    stats = {
        "total_ranked": len(ranked_candidates),
        "max_score": ranked_candidates[0].total_score if ranked_candidates else 0,
        "quota": sch.quota or 0,
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

    quota = sch.quota or 0
    for index, app in enumerate(candidates):
        app.status = "Selected" if index < quota else "Reserved"

    log = DirectorAuditLog(
        user_name="กรรมการ (Admin)",
        action="CONFIRM_SELECTION",
        details=f"ยืนยันผลการคัดเลือกทุน {sch.name} (โควตา {quota} ราย)",
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()

    flash(f"ยืนยันผลการคัดเลือกทุน {sch.name} เรียบร้อยแล้ว", "success")
    return redirect(url_for("director.scholarship_ranking", scholarship_id=scholarship_id))

@director_bp.route("/ranking-selection")
def ranking_selection():
    scholarships = Scholarship.query.all()
    return render_template("director/ranking_selection.html", scholarships=scholarships)

@director_bp.route("/audit_log")
def audit_log():
    all_logs = DirectorAuditLog.query.order_by(DirectorAuditLog.timestamp.desc()).all()
    return render_template("director/audit_log.html", logs=all_logs)