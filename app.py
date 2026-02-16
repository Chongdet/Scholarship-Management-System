from flask import Flask

# 1. นำเข้าไฟล์ Route ของแต่ละฝ่าย
from routes.director_routes import director_bp
from routes.officer_routes import officer_bp
from routes.student_routes import student_bp

app = Flask(__name__)

# 2. ลงทะเบียน (Register) ให้ระบบรู้จัก Route ของแต่ละฝ่าย
app.register_blueprint(director_bp, url_prefix='/director')
app.register_blueprint(officer_bp, url_prefix='/officer')
app.register_blueprint(student_bp, url_prefix='/student')

# 3. Route หน้าแรกสุด (Homepage) อนุโลมให้เอาไว้ที่นี่ได้
@app.route('/')
def home():
    return "หน้าแรกของระบบ Scholarship Management"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)