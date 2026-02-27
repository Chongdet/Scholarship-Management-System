from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==========================================
# ส่วนที่ 1: ระบบผู้ใช้งาน (แยก 3 ตาราง)
# ==========================================

# 1.1 ข้อมูลเจ้าหน้าที่ (Officer)
class Officer(db.Model):
    __tablename__ = 'officer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True) # ชื่อ-นามสกุลเจ้าหน้าที่

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 1.2 ข้อมูลกรรมการ (Director)
class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True) # ชื่อ-นามสกุลกรรมการ

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 1.3 ข้อมูลนักศึกษา (Student)
# models.py (เฉพาะส่วนของ Student)
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    
    # --- 1. ข้อมูลส่วนตัวและการติดต่อ ---
    citizen_id = db.Column(db.String(13))       # [REG]
    address_domicile = db.Column(db.Text)       # [REG]
    email = db.Column(db.String(100))           # [REG]
    mobile = db.Column(db.String(20))           # [REG/Editable]
    address_current = db.Column(db.Text)        # [Self]
    facebook = db.Column(db.String(100))        # [Self]
    line_id = db.Column(db.String(100))         # [Self]

    # --- 2. ข้อมูลการศึกษา [ดึงจาก REG ทั้งหมด] ---
    faculty = db.Column(db.String(100))
    year = db.Column(db.String(10))             # เช่น "ปี 1"
    gpax = db.Column(db.Float)
    advisor_name = db.Column(db.String(100))
    disciplinary_status = db.Column(db.String(50))

    # --- 3. ข้อมูลครอบครัว ---
    father_name = db.Column(db.String(100))     # [REG]
    mother_name = db.Column(db.String(100))     # [REG]
    
    father_job = db.Column(db.String(100))      # [Self]
    father_income = db.Column(db.Float)         # [Self]
    inc_father = db.Column(db.Float)            # [Self] เงินที่บิดาส่งให้ [NEW]
    father_health = db.Column(db.Text)          # [Self]
    
    mother_job = db.Column(db.String(100))      # [Self]
    mother_income = db.Column(db.Float)         # [Self]
    inc_mother = db.Column(db.Float)            # [Self] เงินที่มารดาส่งให้ [NEW]
    mother_health = db.Column(db.Text)          # [Self] ปัญหาสุขภาพมารดา [NEW]
    
    parents_status = db.Column(db.String(50))   # [Self]
    
    # ข้อมูลที่อยู่อาศัย (ขยายเพิ่ม)
    housing_status = db.Column(db.String(100))  # [Self]
    rent_amount = db.Column(db.Float)           # [Self] ค่าเช่าบ้าน [NEW]
    housing_other = db.Column(db.String(100))   # [Self] ระบุที่อยู่อาศัยอื่นๆ [NEW]
    
    # ข้อมูลที่ดินเกษตร (ขยายเพิ่ม)
    land_status = db.Column(db.String(100))     # [Self]
    agri_own_amount = db.Column(db.Float)       # [Self] จำนวนที่ดินตัวเอง (ไร่) [NEW]
    agri_rent_amount = db.Column(db.Float)      # [Self] จำนวนที่ดินเช่า (ไร่) [NEW]
    agri_rent_cost = db.Column(db.Float)        # [Self] ค่าเช่าที่ดิน (บาท/เดือน) [NEW]
    agri_other_detail = db.Column(db.String(100)) # [Self] ระบุอาศัยที่ดินผู้อื่น [NEW]

    # ข้อมูลผู้อุปการะ (กรณีไม่ใช่บิดามารดา) [NEW]
    guardian_name = db.Column(db.String(100))     # [Self] [NEW]
    guardian_relation = db.Column(db.String(50))  # [Self] [NEW]
    guardian_job = db.Column(db.String(100))      # [Self] [NEW]
    guardian_income = db.Column(db.Float)         # [Self] [NEW]
    
    siblings_list = db.Column(db.JSON)          # [Self] เก็บเป็น JSON

    # --- 4. สถานะทางการเงินของนักศึกษา ---
    monthly_allowance = db.Column(db.Float)     # [Self] เงินที่ได้รับต่อเดือน
    loan_student_fund = db.Column(db.Boolean)   # [Self] สถานะ กยศ.
    loan_type = db.Column(db.String(100))       # [Self] ประเภทการกู้
    scholarship_history = db.Column(db.JSON)    # [Self] ประวัติรับทุน

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ==========================================
# ส่วนที่ 2: ระบบทุนการศึกษา
# ==========================================

# 2.1 ข้อมูลทุนการศึกษา
class Scholarship(db.Model):
    __tablename__ = 'scholarship'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    criteria = db.relationship('Criterion', backref='scholarship', lazy=True)
    applications = db.relationship('Application', backref='scholarship', lazy=True)

# 2.2 ข้อมูลใบสมัคร
class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(100))
    faculty = db.Column(db.String(100)) # <--- คงไว้ตามที่คุณเพิ่มมา
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    status = db.Column(db.String(20), default='pending')
    reviewing_by = db.Column(db.String(50))
    reviewing_at = db.Column(db.DateTime)

# 2.3 เกณฑ์คะแนน
class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    name = db.Column(db.String(100))
    max_score = db.Column(db.Integer)