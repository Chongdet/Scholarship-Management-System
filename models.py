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
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True) # เพิ่มไว้สำหรับ Login
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    gpax = db.Column(db.Float)
    
    
    # ... (สามารถเพิ่มฟิลด์อื่นๆ ตามที่คุณมีในไฟล์เดิมได้เลย) ...

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
    name = db.Column(db.String(100), nullable=False) # ชื่อทุน
    quota = db.Column(db.Integer, default=0) # จำนวนกี่ทุน
    amount = db.Column(db.Float, nullable=True) # ทุนละเท่าไหร่
    category = db.Column(db.String(50)) # ประเภทของทุน (เช่น ทุนภายใน/ภายนอก)
    start_date = db.Column(db.Date) # วันที่เปิดรับสมัคร                    
    end_date = db.Column(db.Date) # วันที่ปิดรับสมัคร
    provider = db.Column(db.String(100)) # หน่วยงานของทุนนั้นๆ
    
    status = db.Column(db.String(20), default='open')  # สถานะของทุน open(เปิดรับ),checking=close(กำลังตรวจสอบ,ปิดทุน), interview(รายชื่อสัมภาษณ์), announce(รายชื่อได้รับทุน) 
    interview_file_url = db.Column(db.String(500))    # ลิงก์ไฟล์ประกาศสัมภาษณ์
    announce_file_url = db.Column(db.String(500))     # ลิงก์ไฟล์ประกาศคนได้ทุน

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
    status = db.Column(db.String(20), default='รอตรวจสอบ') # <--- สถานะหลังจากกดส่งใบสมัครเสร็จ
    reviewing_by = db.Column(db.String(50))
    reviewing_at = db.Column(db.DateTime)
    status_description = db.Column(db.Text) # <--- สำหรับเก็บนัดหมายหรือเหตุผลจากเจ้าหน้าที่


# 2.3 เกณฑ์คะแนน
class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    name = db.Column(db.String(100))
    max_score = db.Column(db.Integer)