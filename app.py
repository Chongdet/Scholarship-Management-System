from dotenv import load_dotenv
load_dotenv()

from flask import Flask, redirect, url_for, render_template, request, session, flash
from models import db, Student, Officer, Director, Scholarship
from routes.student_routes import student_bp
from routes.officer_routes import officer_bp
from routes.director_routes import director_bp
from services.reg_service import RegService

import os
from datetime import datetime, timedelta


# =========================================================
# 1. Application Factory
# =========================================================

def create_app():
    app = Flask(__name__)

    thai_months = [
        "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
        "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]

    @app.template_filter("thai_date")
    def thai_date(value):
        if not value:
            return "-"
        if not isinstance(value, datetime):
            return str(value)

        thai_year = value.year + 543
        month = thai_months[value.month - 1]
        return f"{value.day} {month} {thai_year} {value.strftime('%H:%M')} น."

    # -------------------------
    # Configuration
    # -------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "scholarship.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB upload limit

    # -------------------------
    # Initialize Extensions
    # -------------------------
    db.init_app(app)

    # -------------------------
    # Register Blueprints
    # -------------------------
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(officer_bp, url_prefix="/officer")
    app.register_blueprint(director_bp, url_prefix="/director")

    # -------------------------
    # Register Routes
    # -------------------------
    register_routes(app)

    # -------------------------
    # Database Initialization
    # -------------------------
    with app.app_context():
        db.create_all()
        seed_basic_data()

    return app


# =========================================================
# 2. Routes
# =========================================================

def register_routes(app):

    @app.route("/")
    def index():
        scholarships = Scholarship.query.all()
        return render_template("index.html", scholarships=scholarships)


    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            role_target = request.form.get("role")

            if not username or not password:
                flash("กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน", "error")
                return render_template("login.html")

            # -------------------------------------------------
            # STUDENT LOGIN (REG Sync)
            # -------------------------------------------------
            if not role_target:
                success, reg_data = RegService.validate_credentials(username, password)

                if success:
                    student = Student.query.filter_by(student_id=username).first()

                    if not student:
                        student = Student(student_id=username)
                        student.set_password(password)
                        db.session.add(student)

                    # Sync REG data
                    RegService.sync_student_data(student, reg_data)
                    db.session.commit()

                    session.clear()
                    session["user_id"] = student.student_id
                    session["role"] = "student"

                    flash(f"ยินดีต้อนรับคุณ {student.name}", "success")
                    return redirect(url_for("student.dashboard"))

            # -------------------------------------------------
            # OFFICER / DIRECTOR LOGIN
            # -------------------------------------------------
            else:
                user = None

                if role_target == "officer":
                    user = Officer.query.filter_by(username=username).first()
                elif role_target == "director":
                    user = Director.query.filter_by(username=username).first()

                if user and user.check_password(password):
                    session.clear()
                    session["user_id"] = user.username
                    session["role"] = role_target

                    flash(f"ยินดีต้อนรับคุณ {user.name}", "success")

                    if role_target == "officer":
                        return redirect(url_for("officer.list_scholarships"))
                    elif role_target == "director":
                        return redirect(url_for("director.home"))

            flash("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง", "error")

        return render_template("login.html")


    @app.route("/logout")
    def logout():
        session.clear()
        flash("ออกจากระบบเรียบร้อยแล้ว", "success")
        return redirect(url_for("index"))


# =========================================================
# 3. Seed Basic Data (Dev Only)
# =========================================================

def seed_basic_data():
    """
    สร้างข้อมูลทดสอบเฉพาะตอน dev
    Production ควรปิดส่วนนี้
    """

    if not Officer.query.filter_by(username="admin").first():
        admin = Officer(username="admin", name="ผู้ดูแลระบบหลัก")
        admin.set_password("ubu123456")
        db.session.add(admin)

    if not Director.query.filter_by(username="director").first():
        director = Director(username="director", name="กรรมการพิจารณาทุน")
        director.set_password("ubu123456")
        db.session.add(director)

    db.session.commit()


# =========================================================
# 4. Run Application
# =========================================================

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)