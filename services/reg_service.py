# services/reg_service.py
from datetime import datetime


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
        faculties = [
            "คณะวิทยาศาสตร์",
            "คณะวิศวกรรมศาสตร์",
            "คณะพยาบาลศาสตร์",
            "คณะบริหารศาสตร์"
        ]

        for i in range(1, 11):
            student_id = f"68113400{i:02d}"
            dis_status = "ไม่มี" if i % 4 != 0 else "มี"
            
            mock_db[student_id] = {
                "student_id": student_id,
                "name": f"นักศึกษา ทดสอบที่ {i}",
                "faculty": faculties[i % len(faculties)],
                "year": 2,  # ใช้ integer
                "gpax": round(2.5 + (i * 0.15), 2),
                "advisor_name": f"ผศ.ดร. ที่ปรึกษา ใจดี_{i}",
                "disciplinary_status": dis_status,
                "email": f"student{i}@ubu.ac.th",
                "citizen_id": f"1234567890{i:02d}",
                "address_domicile": f"บ้านเลขที่ {i}/99 ต.ในเมือง อ.เมือง จ.อุบลราชธานี",
                "address_current": f"หอพักนักศึกษา อาคาร {i} มหาวิทยาลัยอุบลราชธานี",
                "father_name": f"นายสมชาย ทดสอบ (บิดา {i})",
                "mother_name": f"นางสมศรี ทดสอบ (มารดา {i})"
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

        # --------------------------------
        # 🔓 FULLY EDITABLE (ไม่ผูก REG)
        # --------------------------------
        # father_name / mother_name
        # ไม่ดึงจาก REG อีกต่อไป
        # ให้ระบบทุนเป็นแหล่งข้อมูลหลักแทน

        return student_model