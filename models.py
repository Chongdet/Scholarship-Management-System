from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 1. ข้อมูลรายชื่อทุน
class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # เชื่อมไปยังเกณฑ์และผู้สมัคร
    criteria = db.relationship('Criterion', backref='scholarship', lazy=True)
    applications = db.relationship('Application', backref='scholarship', lazy=True)

# 2. เกณฑ์การให้คะแนน (แยกตามแต่ละทุน)
class Criterion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    name = db.Column(db.String(100))  # เช่น 'คะแนนสัมภาษณ์', 'จิตอาสา'
    max_score = db.Column(db.Integer) # คะแนนเต็มของหัวข้อนั้น

# 3. ข้อมูลผู้สมัครและการให้คะแนน
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(100))
    gpa = db.Column(db.String(10))  # <--- เพิ่มบรรทัดนี้ครับ
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    total_score = db.Column(db.Integer, default=0)
    is_scored = db.Column(db.Boolean, default=False)