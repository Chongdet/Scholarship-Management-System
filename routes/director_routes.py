from datetime import datetime
from flask import render_template, url_for, redirect, flash, request

from flask import Blueprint, render_template, request, redirect, url_for
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
        passed_docs = Application.query.filter_by(
            scholarship_id=sch.id, status="approved"
        ).count()

        scholarship_list.append(
            {
                "id": sch.id,  # 🟢 แก้ให้คีย์ชื่อ "id" และรับค่า sch.id
                "name": sch.name,  # 🟢 แก้ให้คีย์ชื่อ "name" และรับค่า sch.name
                "total_applicants": total_applicants,
                "passed_docs": passed_docs,
            }
        )

    return render_template("director/scoring.html", scholarships=scholarship_list)


# ==========================================
# 2. หน้าแสดงรายชื่อนักศึกษา (แยกตามทุน)
# ==========================================
# 🟢 ใส่ <int:...> เพื่อบังคับให้ URL รับค่าเป็นตัวเลขเท่านั้น (ป้องกัน 404)
@director_bp.route("/scoring/<int:scholarship_id>")
def scholarship_students(scholarship_id):
    # ดึงข้อมูลทุนเพื่อเอาชื่อทุนมาแสดง
    sch = Scholarship.query.get_or_404(scholarship_id)
    # ดึงเฉพาะนักศึกษาที่สมัครทุนนี้เท่านั้น (รายชื่อจะไม่ปนกัน)
    candidates = (
        Application.query.filter(
            Application.scholarship_id == scholarship_id,
            Application.total_score != None,
        )
        .order_by(Application.total_score.desc())
        .all()
    )

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
# 4. หน้าแสดงอันดับนักศึกษา (Ranking)
# เพิ่มต่อท้ายไฟล์เดิม
@director_bp.route("/ranking/<int:scholarship_id>")
def scholarship_ranking(scholarship_id):
    # ดึงข้อมูลทุน
    sch = Scholarship.query.get_or_404(scholarship_id)

    # ดึงเฉพาะคนที่ให้คะแนนแล้ว (is_scored=True) และเรียงคะแนนจากมากไปน้อย
    ranked_candidates = (
        Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)
        .order_by(Application.total_score.desc())
        .all()
    )

    # ข้อมูลสถิติเบื้องต้น
    stats = {
        "total_ranked": len(ranked_candidates),
        "max_score": ranked_candidates[0].total_score if ranked_candidates else 0,
        "quota": sch.quota or 0,
    }

    return render_template(
        "director/ranking.html",
        scholarship=sch,
        candidates=ranked_candidates,
        stats=stats,
    )


# ==========================================
# 4. หน้าดูรายละเอียดนักศึกษา
# ==========================================
@director_bp.route("/candidate/<int:app_id>")
def candidate_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("director/candidate_detail.html", student=application)


@director_bp.route("/confirm_selection/<int:scholarship_id>", methods=["POST"])
def confirm_selection(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)

    # ดึงผู้สมัครที่ผ่านการให้คะแนนแล้ว เรียงตามคะแนนสูงสุด
    candidates = (
        Application.query.filter_by(scholarship_id=scholarship_id, is_scored=True)
        .order_by(Application.total_score.desc())
        .all()
    )

    # อัปเดตสถานะตามโควตา
    quota = sch.quota or 0
    for index, app in enumerate(candidates):
        if index < quota:
            app.status = "Selected"  # ได้รับทุน
        else:
            app.status = "Reserved"  # ตัวสำรอง

    db.session.commit()
    flash(f"ยืนยันผลการคัดเลือกทุน {sch.name} เรียบร้อยแล้ว", "success")
    return redirect(
        url_for("director.scholarship_ranking", scholarship_id=scholarship_id)
    )


@director_bp.route("/ranking-selection")
def ranking_selection():
    # ดึงข้อมูลทุนมาแสดง
    scholarships = Scholarship.query.all()
    return render_template("director/ranking_selection.html", scholarships=scholarships)

# ==========================================
# 5. หน้าบันทึกการทำงาน (Audit Log)
# ==========================================
@director_bp.route("/audit_log")
def audit_log():
    # ในอนาคตคุณสามารถสร้าง Model AuditLog เพื่อเก็บข้อมูลจริงจาก Database ได้
    # ตอนนี้ระบบจะส่ง List ว่างเพื่อให้หน้า HTML แสดงผลได้โดยไม่ Error 404
    logs = [
        # ตัวอย่างข้อมูลจำลอง (Mockup Data)
        # {
        #     "timestamp": datetime.now(),
        #     "user_name": "กรรมการสมชาย",
        #     "action": "ให้คะแนน",
        #     "details": "บันทึกคะแนนนักศึกษา 6401001 ทุนอาหารกลางวัน",
        #     "ip_address": "127.0.0.1"
        # }
    ]
    return render_template("director/audit_log.html", logs=logs)
