from flask import Blueprint, app, render_template, request, redirect, url_for
from models import db, Scholarship, Criterion, Application

director_bp = Blueprint("director", __name__)


# ==========================================
# 1. หน้าแสดงรายการทุนทั้งหมด
# ==========================================
@director_bp.route("/")
def home():
    # หน้าแรกของระบบ (สามารถเข้าผ่าน /director/ ได้)
    return render_template("director/homepage.html")


@director_bp.route("/scoring")
def scoring():
    # ดึงรายชื่อทุนทั้งหมดจาก Database
    scholarships = Scholarship.query.all()

    # สร้าง List ข้อมูลใหม่เพื่อคำนวณจำนวนผู้สมัคร
    scholarship_list = []
    for sch in scholarships:
        # นับจำนวนผู้สมัครทั้งหมดของทุนนี้
        total_applicants = Application.query.filter_by(scholarship_id=sch.id).count()
        # นับจำนวนคนที่ผ่านเอกสาร (สมมติว่าเช็คจาก gpa ว่ามีข้อมูลแล้ว)
        passed_docs = Application.query.filter_by(scholarship_id=sch.id).count()

        scholarship_list.append(
            {
                "id": sch.id,
                "name": sch.name,
                "total_applicants": total_applicants,
                "passed_docs": passed_docs,
            }
        )

    return render_template("director/scoring.html", scholarships=scholarship_list)


# ==========================================
# 2. หน้าแสดงรายชื่อนักศึกษา (แยกตามทุน)
# ==========================================
@director_bp.route("/scoring/<int:scholarship_id>")
def scholarship_students(scholarship_id):
    # ดึงข้อมูลทุนเพื่อเอาชื่อทุนมาแสดง
    sch = Scholarship.query.get_or_404(scholarship_id)
    # ดึงเฉพาะนักศึกษาที่สมัครทุนนี้เท่านั้น (รายชื่อจะไม่ปนกัน)
    candidates = Application.query.filter_by(scholarship_id=scholarship_id).all()

    return render_template(
        "director/scoring_students.html",
        scholarship_id=scholarship_id,
        scholarship_name=sch.name,
        candidates=candidates,
    )


# ==========================================
# 3. หน้าให้คะแนน (ดึงเกณฑ์คะแนนตามทุน)
# ==========================================
@director_bp.route("/score_candidate/<int:app_id>", methods=["GET", "POST"])
def give_score(app_id):
    # ดึงข้อมูลการสมัครของนักศึกษาคนนี้
    application = Application.query.get_or_404(app_id)
    # ดึงเกณฑ์คะแนน (Criteria) เฉพาะของทุนที่นักศึกษาคนนี้สมัคร
    criteria = Criterion.query.filter_by(
        scholarship_id=application.scholarship_id
    ).all()

    if request.method == "POST":
        total = 0
        # วนลูปรับคะแนนตามจำนวนเกณฑ์ที่มีใน Database
        for c in criteria:
            # รับค่าจาก input ที่ชื่อ 'score_IDเกณฑ์' (จะสัมพันธ์กับหน้า HTML)
            score_val = request.form.get(f"score_{c.id}", 0)
            total += int(score_val)

        # บันทึกคะแนนรวมลงใน Database
        application.total_score = total
        application.is_scored = True
        db.session.commit()

        return redirect(
            url_for(
                "director.scholarship_students",
                scholarship_id=application.scholarship_id,
            )
        )

    return render_template(
        "director/give_score.html", student=application, criteria=criteria
    )


# ==========================================
# 4. หน้าดูรายละเอียดนักศึกษา
# ==========================================
@director_bp.route("/candidate/<int:app_id>")
def candidate_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("director/candidate_detail.html", student=application)
