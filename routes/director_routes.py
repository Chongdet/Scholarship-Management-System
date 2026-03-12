from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
# ตรวจสอบว่าใน models.py มีการสร้างคลาส AuditLog ตามที่คุยกันไว้ก่อนหน้าแล้ว
from models import db, Scholarship, Criterion, Application, DirectorAuditLog 

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
        passed_docs = Application.query.filter_by(
            scholarship_id=sch.id, status="approved"
        ).count()

        scholarship_list.append({
            "id": sch.id,
            "name": sch.name,
            "total_applicants": total_applicants,
            "passed_docs": passed_docs,
        })
    return render_template("director/scoring.html", scholarships=scholarship_list)

# ==========================================
# 2. หน้าแสดงรายชื่อนักศึกษา (แยกตามทุน)
# ==========================================
@director_bp.route("/scoring/<int:scholarship_id>")
def scholarship_students(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    # แสดงนักศึกษาที่ผ่านเอกสารแล้วเพื่อให้คะแนน
    candidates = Application.query.filter_by(scholarship_id=scholarship_id, status="approved").all()
    
    return render_template(
        "director/scoring_students.html",
        scholarship_id=scholarship_id,
        scholarship_name=sch.name,
        candidates=candidates,
    )

# ==========================================
# 3. หน้าให้คะแนน (พร้อมบันทึก Audit Log)
# ==========================================
@director_bp.route("/score_candidate/<int:app_id>", methods=["GET", "POST"])
def give_score(app_id):
    application = Application.query.get_or_404(app_id)
    criteria = Criterion.query.filter_by(scholarship_id=application.scholarship_id).all()

    if request.method == "POST":
        total = 0
        for c in criteria:
            score_val = request.form.get(f"score_{c.id}", 0)
            total += int(score_val)

        application.total_score = total
        application.is_scored = True
        
        # 🟢 บันทึก Audit Log เมื่อมีการให้คะแนน
        log = DirectorAuditLog(
            user_name="กรรมการ (Admin)", # ในอนาคตเปลี่ยนเป็น current_user.name
            action="SCORING",
            details=f"ให้คะแนนนักศึกษา {application.student_name} รหัส {application.student_id} ทุน {application.scholarship.name} คะแนนรวม {total}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash(f"บันทึกคะแนนของ {application.student_name} เรียบร้อยแล้ว", "success")
        return redirect(url_for("director.scholarship_students", scholarship_id=application.scholarship_id))

    return render_template("director/give_score.html", student=application, criteria=criteria)

# ==========================================
# 4. หน้าจัดอันดับและยืนยันผล (พร้อมบันทึก Audit Log)
# ==========================================
@director_bp.route("/ranking/<int:scholarship_id>")
def scholarship_ranking(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    ranked_candidates = Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)\
        .order_by(Application.total_score.desc()).all()

    stats = {
        "total_ranked": len(ranked_candidates),
        "max_score": ranked_candidates[0].total_score if ranked_candidates else 0,
        "quota": sch.quota or 0,
    }
    return render_template("director/ranking.html", scholarship=sch, candidates=ranked_candidates, stats=stats)

@director_bp.route("/confirm_selection/<int:scholarship_id>", methods=["POST"])
def confirm_selection(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    candidates = Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)\
        .order_by(Application.total_score.desc()).all()

    quota = sch.quota or 0
    for index, app in enumerate(candidates):
        if index < quota:
            app.status = "Selected"
        else:
            app.status = "Reserved"

    # 🟢 บันทึก Audit Log เมื่อมีการยืนยันผลประกาศชื่อ
    log = DirectorAuditLog(
        user_name="กรรมการ (Admin)",
        action="CONFIRM_SELECTION",
        details=f"ยืนยันผลการคัดเลือกและประกาศชื่อผู้ได้รับทุน {sch.name} (โควตา {quota} ราย)",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f"ยืนยันผลการคัดเลือกทุน {sch.name} เรียบร้อยแล้ว", "success")
    return redirect(url_for("director.scholarship_ranking", scholarship_id=scholarship_id))

@director_bp.route("/ranking-selection")
def ranking_selection():
    scholarships = Scholarship.query.all()
    return render_template("director/ranking_selection.html", scholarships=scholarships)

# ==========================================
# 5. หน้าบันทึกการทำงาน (Audit Log) - ดึงข้อมูลจริงจาก DB
# ==========================================
@director_bp.route("/audit_log")
def audit_log():
    # ดึงข้อมูลจากฐานข้อมูลจริง เรียงตามเวลาล่าสุด
    all_logs = DirectorAuditLog.query.order_by(DirectorAuditLog.timestamp.desc()).all()
    return render_template("director/audit_log.html", logs=all_logs)

@director_bp.route("/candidate/<int:app_id>")
def candidate_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("director/candidate_detail.html", student=application)