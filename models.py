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
    citizen_id       = db.Column(db.String(13))   # [REG]
    address_domicile = db.Column(db.Text)          # [REG]
    email            = db.Column(db.String(100))   # [REG]
    mobile           = db.Column(db.String(20))    # [REG/Editable]
    address_current  = db.Column(db.Text)          # [Self]
    facebook         = db.Column(db.String(100))   # [Self]
    line_id          = db.Column(db.String(100))   # [Self]

    # --- 2. ข้อมูลการศึกษา [ดึงจาก REG ทั้งหมด] ---
    faculty              = db.Column(db.String(100))
    year                 = db.Column(db.String(10))   # เช่น "ปี 1"
    gpax                 = db.Column(db.Float)
    advisor_name         = db.Column(db.String(100))
    disciplinary_status  = db.Column(db.String(50))

    # --- 3. ข้อมูลครอบครัว ---
    father_name   = db.Column(db.String(100))  # [REG]
    mother_name   = db.Column(db.String(100))  # [REG]

    father_job    = db.Column(db.String(100))  # [Self]
    father_income = db.Column(db.Float)        # [Self] รายได้บิดา/เดือน
    inc_father    = db.Column(db.Float)        # [Self] เงินที่บิดาส่งให้/เดือน
    father_health = db.Column(db.Text)         # [Self]

    mother_job    = db.Column(db.String(100))  # [Self]
    mother_income = db.Column(db.Float)        # [Self] รายได้มารดา/เดือน
    inc_mother    = db.Column(db.Float)        # [Self] เงินที่มารดาส่งให้/เดือน
    mother_health = db.Column(db.Text)         # [Self] ปัญหาสุขภาพมารดา

    parents_status = db.Column(db.String(50))  # [Self]

    # ข้อมูลที่อยู่อาศัย
    housing_status = db.Column(db.String(100)) # [Self]
    rent_amount    = db.Column(db.Float)        # [Self] ค่าเช่าบ้าน/เดือน
    housing_other  = db.Column(db.String(100)) # [Self] ระบุที่อยู่อาศัยอื่นๆ

    # ข้อมูลที่ดินเกษตร
    land_status       = db.Column(db.String(100))  # [Self]
    agri_own_amount   = db.Column(db.Float)         # [Self] จำนวนที่ดินตัวเอง (ไร่)
    agri_rent_amount  = db.Column(db.Float)         # [Self] จำนวนที่ดินเช่า (ไร่)
    agri_rent_cost    = db.Column(db.Float)         # [Self] ค่าเช่าที่ดิน (บาท/เดือน)
    agri_other_detail = db.Column(db.String(100))   # [Self] ระบุอาศัยที่ดินผู้อื่น

    # ข้อมูลผู้อุปการะ (กรณีไม่ใช่บิดามารดา)
    guardian_name     = db.Column(db.String(100))  # [Self]
    guardian_relation = db.Column(db.String(50))   # [Self]
    guardian_job      = db.Column(db.String(100))  # [Self]
    guardian_income   = db.Column(db.Float)         # [Self]

    siblings_list = db.Column(db.JSON)  # [Self] เก็บเป็น JSON

    # --- 4. รายได้และค่าใช้จ่ายนักศึกษาต่อเดือน ---
    # รายได้ที่นักศึกษาได้รับ
    inc_guardian    = db.Column(db.Float)  # [Self] ได้รับจากผู้อุปการะ
    inc_scholarship = db.Column(db.Float)  # [Self] ได้รับจากทุนการศึกษา (เฉลี่ยรายเดือน)
    inc_parttime    = db.Column(db.Float)  # [Self] ได้รับจากการทำงาน Part time

    # ค่าใช้จ่ายนักศึกษา
    exp_food        = db.Column(db.Float)  # [Self] ค่าอาหาร
    exp_dorm        = db.Column(db.Float)  # [Self] ค่าหอพัก
    exp_transport   = db.Column(db.Float)  # [Self] ค่าพาหนะ/เดินทาง
    exp_other       = db.Column(db.Float)  # [Self] ค่าใช้จ่ายอื่นๆ

    # --- 5. สถานะ กยศ. และทุนการศึกษา ---
    monthly_allowance  = db.Column(db.Float)        # [Self] เงินที่ได้รับต่อเดือน (รวม)
    loan_student_fund  = db.Column(db.Boolean)      # [Self] สถานะ กยศ.
    loan_type          = db.Column(db.String(100))  # [Self] ประเภทการกู้
    scholarship_history = db.Column(db.JSON)        # [Self] ประวัติรับทุน

    # --- 6. ข้อมูลคำนวณและสถานะระบบ ---
    profile_completeness    = db.Column(db.Integer, default=0)    # คะแนนความสมบูรณ์ของโปรไฟล์ (0-100)
    total_family_income     = db.Column(db.Float,   default=0.0)  # รายได้รวมครอบครัว (คำนวณอัตโนมัติ)
    financial_hardship_score = db.Column(db.Float,  default=0.0)  # ดัชนีความลำบากทางการเงิน (0-1)
    is_profile_locked       = db.Column(db.Boolean, default=False) # ล็อกโปรไฟล์หลังส่งใบสมัคร
    profile_pic = db.Column(db.String(500), nullable=True)  # URL of profile picture
    # ──────────────────────────────────────────────────────────────
    def calculate_total_income(self):
        """คำนวณรายได้รวมครอบครัว: บิดา + มารดา + ผู้อุปการะ"""
        total = (
            (self.father_income   or 0.0) +
            (self.mother_income   or 0.0) +
            (self.guardian_income or 0.0)
        )
        self.total_family_income = total
        return total

    def calculate_student_income(self):
        """คำนวณรายได้รวมที่นักศึกษาได้รับต่อเดือน"""
        total = (
            (self.inc_father      or 0.0) +
            (self.inc_mother      or 0.0) +
            (self.inc_guardian    or 0.0) +
            (self.inc_scholarship or 0.0) +
            (self.inc_parttime    or 0.0)
        )
        self.monthly_allowance = total
        return total

    def calculate_student_expense(self):
        """คำนวณค่าใช้จ่ายรวมของนักศึกษาต่อเดือน"""
        total = (
            (self.exp_food      or 0.0) +
            (self.exp_dorm      or 0.0) +
            (self.exp_transport or 0.0) +
            (self.exp_other     or 0.0)
        )
        return total

    def update_completeness(self):
        """คำนวณความสมบูรณ์ของโปรไฟล์จากฟิลด์ที่กำหนด"""
        required_fields = [
            'address_current', 'mobile', 'father_job', 'mother_job', 'housing_status'
        ]
        filled = sum(1 for field in required_fields if getattr(self, field))
        self.profile_completeness = int((filled / len(required_fields)) * 100)
        return self.profile_completeness

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
    amount = db.Column(db.Float, nullable=True) # ทุนละเท่าไหร่

    # --- เงื่อนไขการรับสมัคร ---
    start_date        = db.Column(db.DateTime)          # วันที่เริ่มเปิดรับ
    end_date          = db.Column(db.DateTime)          # วันที่ปิดรับ
    faculty_condition = db.Column(db.String(255))       # คณะที่ระบุ หรือ "ทุกคณะ"
    min_gpax          = db.Column(db.Float, default=0.0) # เกรดเฉลี่ยขั้นต่ำ
    income_cap        = db.Column(db.Float)             # รายได้ครอบครัวไม่เกิน
    number_of_scholarships = db.Column(db.Integer)           # จำนวนทุนที่เปิดรับ
    scholarship_type  = db.Column(db.String(50)) # ประเภทของทุน (เช่น ทุน ภายใน/ภายนอก/บริจาค)
    provider          = db.Column(db.String(100)) # หน่วยงานของทุนนั้นๆ
    status            = db.Column(db.String(20), default='open')  # สถานะของทุน open(เปิดรับ),checking=close(กำลังตรวจสอบ,ปิดทุน), interview(รายชื่อสัมภาษณ์), announce(รายชื่อได้รับทุน)
    interview_file_url = db.Column(db.String(500))    # ลิงก์ไฟล์ประกาศสัมภาษณ์
    announce_file_url = db.Column(db.String(500))     # ลิงก์ไฟล์ประกาศคนได้ทุน

    # ฟิลด์ใหม่สำหรับรายละเอียดทุนการศึกษา
    image = db.Column(db.String(200), nullable=True) # ชื่อไฟล์ภาพ
    qualifications = db.Column(db.Text, nullable=True) # คุณสมบัติ
    conditions = db.Column(db.Text, nullable=True) # เงื่อนไข
    scholarship_nature = db.Column(db.String(50), nullable=True) # ลักษณะทุน (ทุนรายปี, ฯลฯ)
    required_documents = db.Column(db.Text, nullable=True) # เอกสารที่ต้องส่ง

    criteria     = db.relationship('Criterion',   backref='scholarship', lazy=True)

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
    faculty = db.Column(db.String(100)) # <--- คงไว้ตามที่คุณเพิ่มมา
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
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
    notes = db.Column(db.Text, nullable=True) # เหตุผล/ข้อมูลเพิ่มเติมจากนักศึกษา
    form_data = db.Column(db.Text, nullable=True) # JSON ข้อมูลเต็มจากฟอร์มสมัคร

    @property
    def gpa(self):
        """GPA จาก Student (gpax)"""
        s = Student.query.filter_by(student_id=self.student_id).first()
        return s.gpax if s and s.gpax is not None else "-"

    @property
    def application_date(self):
        """วันที่สมัคร (alias ของ created_at)"""
        return self.created_at.strftime('%d/%m/%Y') if self.created_at else "-"

# 2.3 ตารางการประเมินผลคะแนน (Evaluation)
class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    evaluation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.String, db.ForeignKey('application.id'), nullable=False)
    committee_id = db.Column(db.String(50), nullable=True) # กรรมการท่านไหนเป็นคนให้คะแนน
    score_financial = db.Column(db.Integer, default=0) # คะแนนความจำเป็น (เต็ม 30)
    score_interview = db.Column(db.Integer, default=0) # คะแนนสัมภาษณ์ (เต็ม 50)
    score_volunteer = db.Column(db.Integer, default=0) # คะแนนจิตอาสา (เต็ม 20)
    
    application = db.relationship('Application', backref=db.backref('evaluations', lazy=True))

# 2.4 บันทึกการทำงาน (Audit Log)
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
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    name = db.Column(db.String(100))
    max_score = db.Column(db.Integer)


# บันทึกการทำงานฝั่งกรรมการ (Director) - ตาราง audit_logs
class DirectorAuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
