from . import db
from werkzeug.security import generate_password_hash, check_password_hash

# --- ข้อมูลเจ้าหน้าที่ (Officer) ---
class Officer(db.Model):
    __tablename__ = 'officer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- ข้อมูลกรรมการ (Director) ---
class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- ข้อมูลนักศึกษา (Student) ---
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    
    # ข้อมูลส่วนตัว
    citizen_id = db.Column(db.String(13))
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    faculty = db.Column(db.String(100))
    year = db.Column(db.String(10))
    gpax = db.Column(db.Float)
    
    # ข้อมูลครอบครัว (ดึงมาจากส่วนที่คุณส่งมา)
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    inc_father = db.Column(db.Float)
    inc_mother = db.Column(db.Float)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)