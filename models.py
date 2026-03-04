from datetime import datetime
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


# 2.3 บันทึกการทำงาน (Audit Log) - จากฝั่ง main
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    officer_username = db.Column(db.String(50), nullable=False)  # ชื่อ/รหัสเจ้าหน้าที่
    officer_label = db.Column(db.String(50), nullable=True)      # ฉายาแสดง เช่น เจ้าหน้าที่(A)
    action = db.Column(db.String(50), nullable=False)            # ชนิดการทำงาน
    action_title = db.Column(db.String(100), nullable=True)      # ชื่อการกระทำภาษาไทย 
    reference_id = db.Column(db.String(30), nullable=True)       # รหัสอ้างอิง เช่น APP345, SCH001
    details = db.Column(db.String(500))                          # คำอธิบายรายละเอียด
    status_after = db.Column(db.String(100), nullable=True)      # สถานะหลังแก้ไข/ปัจจุบัน 
    previous_value = db.Column(db.String(200), nullable=True)    # ค่าเดิมก่อนแก้ไข 

# 2.4 เกณฑ์คะแนน
class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    # ผูกกับ scholarship_id ที่เป็น String
    scholarship_id = db.Column(db.String(20), db.ForeignKey('scholarship.scholarship_id'))
    name = db.Column(db.String(100))  # เช่น 'คะแนนสัมภาษณ์', 'จิตอาสา'
    max_score = db.Column(db.Integer) # คะแนนเต็มของหัวข้อนั้น