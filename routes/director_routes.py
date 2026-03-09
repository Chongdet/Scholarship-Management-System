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
        total_applicants = Application.query.filter_by(scholarship_id=sch.id).count()
        # ผ่านเอกสาร = เจ้าหน้าที่อนุมัติสัมภาษณ์แล้ว (status=interview) หรือกรรมการอนุมัติแล้ว (status=approved)
        passed_docs = Application.query.filter(
            Application.scholarship_id == sch.id,
            Application.status.in_(['interview', 'approved'])
        ).count()

        scholarship_list.append(
            {
                "id": sch.id,
                "name": sch.name,
                "scholarship_id": sch.id,
                "total_applicants": total_applicants,
                "passed_docs": passed_docs,
            }
        )

    return render_template("director/scoring.html", scholarships=scholarship_list)


# ==========================================
# 2. หน้าแสดงรายชื่อนักศึกษา (แยกตามทุน)
# ==========================================
@director_bp.route("/scoring/<scholarship_id>")
def scholarship_students(scholarship_id):
    # ดึงข้อมูลทุนเพื่อเอาชื่อทุนมาแสดง
    sch = Scholarship.query.get_or_404(scholarship_id)
    # ดึงเฉพาะนักศึกษาที่เจ้าหน้าที่อนุมัติสัมภาษณ์แล้ว (status=interview) หรืออนุมัติแล้ว (status=approved)
    candidates = Application.query.filter(
        Application.scholarship_id == scholarship_id,
        Application.status.in_(['interview', 'approved'])
    ).all()

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
            score_val = request.form.get(f"score_{c.id}", 0)
            total += int(score_val or 0)

        # บันทึกคะแนนรวมลงใน Database
        application.total_score = total
        application.is_scored = True

        # ถ้ากดอนุมัติได้รับทุน เปลี่ยน status เป็น approved (สถานะ "ผ่าน" ในฝั่งเจ้าหน้าที่)
        if request.form.get("approve_scholarship") == "1":
            application.status = "approved"

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
# 4. อนุมัติได้รับทุน (ตั้ง status=approved)
# ==========================================
@director_bp.route("/approve/<int:app_id>", methods=["POST"])
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
@director_bp.route("/candidate/<int:app_id>")
def candidate_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("director/candidate_detail.html", student=application)
