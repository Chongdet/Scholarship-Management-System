from flask import Blueprint, render_template

director_bp = Blueprint('director', __name__)

# ==========================================
# ผู้รับผิดชอบ: นาย ทรงเดช จำปาเทศ
# ==========================================

@director_bp.route('/scoring', methods=['GET', 'POST'])
def scoring():
    """ระบบคำนวณคะแนน (Scoring & Calculation System)"""
    return "Director: Scoring & Calculation System"

@director_bp.route('/ranking')
def ranking():
    """ระบบจัดอันดับและตัดสินผล (Ranking & Selection Finalizations)"""
    return "Director: Ranking & Selection Finalizations"


# ==========================================
# ผู้รับผิดชอบ: นาย กฤชณัท ศิริรังสรรค์กุล
# ==========================================

@director_bp.route('/candidates')
def candidates_list():
    """ดูรายชื่อผู้สมัคร (Candidate List)"""
    return "Director: Candidate List"

@director_bp.route('/candidate/<int:student_id>')
def candidate_detail(student_id):
    """ตรวจสอบรายละเอียดผู้สมัครรายบุคคล (Detail Review)"""
    return f"Director: Reviewing Details for Candidate ID: {student_id}"