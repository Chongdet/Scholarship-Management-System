from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 1. ข้อมูลรายชื่อทุน
class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=True)  # จำนวนเงินทุน
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
    faculty = db.Column(db.String(100))
    gpa = db.Column(db.String(10)) 
    application_date = db.Column(db.String(20))
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    total_score = db.Column(db.Integer, default=0)
    is_scored = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

# 4. ข้อมูลนักศึกษา (เพิ่มโดยทีมงานจาก Feature Login)
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    
    # --- ข้อมูลระบุตัวตนและการติดต่อ (Contact Info) ---
    name = db.Column(db.String(100), nullable=False)
    citizen_id = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(100))
    facebook = db.Column(db.String(100))
    line_id = db.Column(db.String(100))
    address_domicile = db.Column(db.Text)
    address_current = db.Column(db.Text)

    # --- ข้อมูลการศึกษา (Academic) ---
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    faculty = db.Column(db.String(100))
    year = db.Column(db.Integer)
    gpax = db.Column(db.Float)
    advisor_name = db.Column(db.String(100))
    disciplinary_status = db.Column(db.String(50)) 

    # --- ประวัติการขอทุนและกู้ยืม ---
    loan_student_fund = db.Column(db.Boolean, default=False)
    loan_type = db.Column(db.String(50))
    scholarship_history = db.Column(db.JSON) 

    # --- ข้อมูลการทำงานและรายได้ ---
    inc_father = db.Column(db.Float, default=0.0)
    inc_mother = db.Column(db.Float, default=0.0)
    inc_guardian = db.Column(db.Float, default=0.0)

    # --- ข้อมูลครอบครัว (Family Info) ---
    father_name = db.Column(db.String(100))
    father_job = db.Column(db.String(100))
    father_income = db.Column(db.Float, default=0.0)
    father_health = db.Column(db.String(200))
    mother_name = db.Column(db.String(100))
    mother_job = db.Column(db.String(100))
    mother_income = db.Column(db.Float, default=0.0)
    parents_status = db.Column(db.String(50))
    housing_status = db.Column(db.String(50))
    land_status = db.Column(db.String(50))
    land_size = db.Column(db.Float, default=0.0)
    siblings_list = db.Column(db.JSON)