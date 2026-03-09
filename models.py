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
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False) # ชื่อทุน
    quota = db.Column(db.Integer, default=0) # จำนวนกี่ทุน
    amount = db.Column(db.Float, nullable=True) # ทุนละเท่าไหร่
    category = db.Column(db.String(50)) # ประเภทของทุน (เช่น ทุนภายใน/ภายนอก)
    start_date = db.Column(db.Date) # วันที่เปิดรับสมัคร                    
    end_date = db.Column(db.Date) # วันที่ปิดรับสมัคร
    provider = db.Column(db.String(100)) # หน่วยงานของทุนนั้นๆ
    min_gpax = db.Column(db.Float, nullable=True)   
    income_cap = db.Column(db.Float, nullable=True) # กำหนดเพดานรายได้ (ถ้ามี)  
    status = db.Column(db.String(20), default='open')  # สถานะของทุน open(เปิดรับ),checking=close(กำลังตรวจสอบ,ปิดทุน), interview(รายชื่อสัมภาษณ์), announce(รายชื่อได้รับทุน) 
    interview_file_url = db.Column(db.String(500))    # ลิงก์ไฟล์ประกาศสัมภาษณ์
    announce_file_url = db.Column(db.String(500))     # ลิงก์ไฟล์ประกาศคนได้ทุน
    faculty_condition = db.Column(db.String(100), nullable=True) # หรือเป็น Text ก็ได้
    
    # ฟิลด์ใหม่สำหรับรายละเอียดทุนการศึกษา
    image = db.Column(db.String(200), nullable=True) # ชื่อไฟล์ภาพ
    qualifications = db.Column(db.Text, nullable=True) # คุณสมบัติ
    conditions = db.Column(db.Text, nullable=True) # เงื่อนไข
    scholarship_type = db.Column(db.String(50), nullable=True) # ประเภททุน (ทุนบริจาค, ฯลฯ)
    scholarship_nature = db.Column(db.String(50), nullable=True) # ลักษณะทุน (ทุนรายปี, ฯลฯ)
    number_of_scholarships = db.Column(db.Integer, default=1) # จำนวนทุน
    required_documents = db.Column(db.Text, nullable=True) # เอกสารที่ต้องส่ง
    
    criteria = db.relationship('Criterion', backref='scholarship', lazy=True)
    applications = db.relationship('Application', backref='scholarship', lazy=True)

    def is_open(self):
        """เช็คว่าทุนเปิดอยู่และยังไม่หมดเขต"""
        now = datetime.now()
        if self.status != "open": # เปลี่ยนเป็นพิมพ์เล็กให้ตรงกับค่า default
            return False
        if self.start_date and self.end_date:
            return self.start_date <= now.date() <= self.end_date # เปรียบเทียบ date() ให้ตรงกัน
        return True

    def __repr__(self):
        return f"<Scholarship {self.name}>" # เปลี่ยนเป็น self.name เพราะตารางนี้ไม่มี scholarship_name


# 2.2 ข้อมูลใบสมัคร
class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.String, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    
    scholarship_id = db.Column(db.String(20), db.ForeignKey('scholarship.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    reviewing_by = db.Column(db.String(50))
    reviewing_at = db.Column(db.DateTime)
    status_description = db.Column(db.Text)
    is_scored = db.Column(db.Boolean, default=False)
    total_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) #เก็บวันที่สมัคร
    application_file = db.Column(db.String(200), nullable=True) #เอกสารไฟล์เเนบของนักศึกษา

    reject_reason = db.Column(db.Text, nullable=True) #เหตุผลจากเจ้าหน้าที่
    interview_date = db.Column(db.Date, nullable=True) # วันที่นัดสัมภาษณ์
    interview_time = db.Column(db.String(100), nullable=True) # เเวลานัดสัมภาษณ์
    interview_location = db.Column(db.String(255), nullable=True) #สถานที่นัดสัมภาษณ์

# 2.3 บันทึกการทำงาน (Audit Log)
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
    
    # ✅ แก้ไขตรงนี้: เปลี่ยนเป็น db.Integer และอ้างอิงไปที่ scholarship.id
    scholarship_id = db.Column(db.String(20), db.ForeignKey('scholarship.id'))
    
    name = db.Column(db.String(100))  # เช่น 'คะแนนสัมภาษณ์', 'จิตอาสา'
    max_score = db.Column(db.Integer) # คะแนนเต็มของหัวข้อนั้น
    
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    user_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # เช่น 'GIVE_SCORE', 'CONFIRM_SELECTION'
    details = db.Column(db.Text, nullable=True)         # เช่น 'ให้คะแนนนักศึกษา นาย A รวม 85 คะแนน'
    ip_address = db.Column(db.String(45), nullable=True)

    def __init__(self, user_name, action, details, ip_address):
        self.user_name = user_name
        self.action = action
        self.details = details
        self.ip_address = ip_address
    