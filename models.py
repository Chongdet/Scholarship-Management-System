from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. ข้อมูลรายชื่อทุน
class Scholarship(db.Model):
    __tablename__ = "scholarships"

    # รหัสทุน เช่น SCH-2567-01
    scholarship_id = db.Column(db.String(20), primary_key=True)

    # ชื่อทุน
    scholarship_name = db.Column(db.String(150), nullable=False)

    # จำนวนเงิน
    amount = db.Column(db.Float, nullable=True)

    # เกรดขั้นต่ำ
    min_gpax = db.Column(db.Float, nullable=True)

    # เงื่อนไขคณะ (ถ้าเป็น None = รับทุกคณะ)
    faculty_condition = db.Column(db.String(100), nullable=True)

    # วันเปิด - ปิดรับสมัคร
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    # สถานะ Open / Closed
    status = db.Column(db.String(10), default="Open")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ความสัมพันธ์
    criteria = db.relationship('Criterion', backref='scholarship', lazy=True)
    applications = db.relationship('Application', backref='scholarship', lazy=True)

    def is_open(self):
        """เช็คว่าทุนเปิดอยู่และยังไม่หมดเขต"""
        now = datetime.now()

        if self.status != "Open":
            return False

        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date

        return True

    def __repr__(self):
        return f"<Scholarship {self.scholarship_name}>"

# 2. เกณฑ์การให้คะแนน (แยกตามแต่ละทุน)
class Criterion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.String(20), db.ForeignKey('scholarships.scholarship_id'))
    name = db.Column(db.String(100))  # เช่น 'คะแนนสัมภาษณ์', 'จิตอาสา'
    max_score = db.Column(db.Integer) # คะแนนเต็มของหัวข้อนั้น

# 3. ข้อมูลผู้สมัครและการให้คะแนน
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    gpa = db.Column(db.String(10))  # <--- เพิ่มบรรทัดนี้ครับ
    application_date = db.Column(db.String(20))
    scholarship_id = db.Column(db.String(20), db.ForeignKey('scholarships.scholarship_id'))
    total_score = db.Column(db.Integer, default=0)
    is_scored = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

