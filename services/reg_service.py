# services/reg_service.py
from datetime import datetime

import urllib


class RegService:
    """
    REG Service Layer
    - จำลองฐานข้อมูล REG (Authoritative Source)
    - จัดการ validate login
    - Sync ข้อมูลจาก REG มายังระบบทุน
    """

    _mock_db = None  # cache เพื่อลดการ rebuild mock db ทุกครั้ง

    # ==============================
    # Mock REG Database
    # ==============================
    @classmethod
    def _build_mock_db(cls):
        mock_db = {}
        
        # ข้อมูลนักศึกษาจริง (ตรงกับใน seed.py)
        students_data = [
            {"student_id": "6811454001", "name": "นายธนกฤต วงศ์สุวรรณ",      "email": "thanakrit.w@ubu.ac.th",    "faculty": "คณะวิศวกรรมศาสตร์",  "gpax": 3.21},
            {"student_id": "6811454002", "name": "นางสาวพิมพ์ชนก ทองดี",      "email": "pimchanok.t@ubu.ac.th",    "faculty": "คณะวิทยาศาสตร์",     "gpax": 3.56},
            {"student_id": "6811454003", "name": "นายอภิสิทธิ์ ศรีสมบูรณ์",   "email": "apisit.s@ubu.ac.th",      "faculty": "คณะบริหารศาสตร์",    "gpax": 2.89},
            {"student_id": "6811454004", "name": "นางสาวกนกวรรณ แสงจันทร์",   "email": "kanokwan.s@ubu.ac.th",    "faculty": "คณะพยาบาลศาสตร์",    "gpax": 3.78},
            {"student_id": "6811454005", "name": "นายณัฐพงษ์ ใจดี",           "email": "nattapong.j@ubu.ac.th",   "faculty": "คณะวิศวกรรมศาสตร์",  "gpax": 3.10},
            {"student_id": "6811454006", "name": "นางสาวสุภาวดี มีสุข",       "email": "supawadee.m@ubu.ac.th",   "faculty": "คณะศิลปศาสตร์",      "gpax": 3.44},
            {"student_id": "6811454007", "name": "นายวรวุฒิ ประสงค์ดี",       "email": "worawut.p@ubu.ac.th",     "faculty": "คณะวิทยาศาสตร์",     "gpax": 2.95},
            {"student_id": "6811454008", "name": "นางสาวชนิดา รุ่งเรือง",     "email": "chanida.r@ubu.ac.th",     "faculty": "คณะนิติศาสตร์",      "gpax": 3.62},
            {"student_id": "6811454009", "name": "นายปิยะพัฒน์ สุขสงวน",     "email": "piyapat.s@ubu.ac.th",     "faculty": "คณะบริหารศาสตร์",    "gpax": 3.05},
            {"student_id": "6811454010", "name": "นางสาวอารียา ดวงจันทร์",    "email": "areeya.d@ubu.ac.th",     "faculty": "คณะเภสัชศาสตร์",     "gpax": 3.88},
            {"student_id": "6811454011", "name": "นาย ทรงเดช จำปาเทศ",    "email": "chongdet.ja.68@ubu.ac.th", "faculty": "คณะวิทยาศาสตร์",     "gpax": 4.00},
        ]

        for i, data in enumerate(students_data, 1):
            student_id = data["student_id"]
            dis_status = "ไม่มี" if i % 4 != 0 else "มี"
            
            mock_db[student_id] = {
                "student_id": student_id,
                "name": data["name"],
                "faculty": data["faculty"],
                "year": 2, 
                "gpax": data["gpax"],
                "advisor_name": f"ผศ.ดร. ที่ปรึกษา {i+1}",
                "disciplinary_status": dis_status,
                "email": data["email"],
                "citizen_id": f"1234567890{i:02d}",
                "address_domicile": f"บ้านเลขที่ {i}/99 ต.ในเมือง อ.เมือง จ.อุบลราชธานี",
                "address_current": f"หอพักนักศึกษา อาคาร {i} มหาวิทยาลัยอุบลราชธานี",
                "father_name": f"นายสมชาย ทดสอบ (บิดา {i})",
                "mother_name": f"นางสมศรี ทดสอบ (มารดา {i})",
                "profile_pic": f"/static/images/students/{student_id}.jpg"
            }

        return mock_db

    @classmethod
    def _get_mock_db(cls):
        if cls._mock_db is None:
            cls._mock_db = cls._build_mock_db()
        return cls._mock_db

    # ==============================
    # Authentication
    # ==============================
    @classmethod
    def validate_credentials(cls, student_id, password):
        """
        ตรวจสอบ Login
        (จำลองรหัสผ่านกลางเป็น stu123456)
        """
        mock_reg_db = cls._get_mock_db()

        if student_id in mock_reg_db and password == "stu123456":
            return True, mock_reg_db[student_id]

        return False, None

    # ==============================
    # Sync Policy
    # ==============================
    @staticmethod
    def sync_student_data(student_model, reg_data):
        """
        Sync ข้อมูลจาก REG → ระบบทุน

        LOCK fields = ต้องมาจาก REG เท่านั้น
        EDITABLE fields = นักศึกษาแก้ไขได้
        """

        if not reg_data:
            return student_model

        # --------------------------------
        # 🛡️ LOCK (Authoritative from REG)
        # --------------------------------
        student_model.name = reg_data.get('name')
        student_model.faculty = reg_data.get('faculty')
        student_model.gpax = reg_data.get('gpax')
        student_model.year = reg_data.get('year')
        student_model.disciplinary_status = reg_data.get('disciplinary_status')
        student_model.advisor_name = reg_data.get('advisor_name')
        student_model.citizen_id = reg_data.get('citizen_id')
        student_model.address_domicile = reg_data.get('address_domicile')
        if reg_data.get('profile_pic'):
            student_model.profile_pic = reg_data.get('profile_pic')
        # ❌ ไม่ sync student_id (Primary Key ห้ามทับ)

        # --------------------------------
        # 🔓 DEFAULT FROM REG (ดึงมาตั้งต้น แต่แก้ไขได้)
        # --------------------------------
        if not student_model.email:
            student_model.email = reg_data.get('email')

        if not student_model.address_current:
            student_model.address_current = reg_data.get('address_current')

        # 🌟 จุดที่เพิ่ม: ดึงชื่อบิดาและมารดามาด้วย ถ้ายังไม่มีข้อมูล
        if not student_model.father_name:
            student_model.father_name = reg_data.get('father_name')

        if not student_model.mother_name:
            student_model.mother_name = reg_data.get('mother_name')

        return student_model
