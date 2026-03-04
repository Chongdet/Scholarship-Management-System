# services/matching_service.py
from datetime import datetime

class MatchingService:
    @staticmethod
    def check_eligibility(student, scholarship):
        """
        ตรวจสอบว่านักศึกษาคนนี้สมัครทุนที่ระบุได้หรือไม่
        ส่งกลับเป็น (bool, [list of reasons])
        """
        is_eligible = True
        reasons = []

        # 1. ตรวจสอบเกรดขั้นต่ำ
        if scholarship.min_gpax and student.gpax < scholarship.min_gpax:
            is_eligible = False
            reasons.append(f"เกรดเฉลี่ย ({student.gpax}) ต่ำกว่าที่ทุนกำหนด ({scholarship.min_gpax})")

        # 2. ตรวจสอบคณะ
        if scholarship.faculty_condition and scholarship.faculty_condition != "ทุกคณะ":
            if student.faculty != scholarship.faculty_condition:
                is_eligible = False
                reasons.append(f"ทุนนี้สำหรับ {scholarship.faculty_condition} เท่านั้น")

        # 3. ตรวจสอบรายได้ครอบครัว (ถ้ามีการระบุ Income Cap)
        student.calculate_total_income() # เรียกใช้ method จาก models.py
        if scholarship.income_cap and student.total_family_income > scholarship.income_cap:
            is_eligible = False
            reasons.append(f"รายได้ครอบครัวเกินเกณฑ์ที่กำหนด")

        # 4. ตรวจสอบวันปิดรับสมัคร
        if scholarship.end_date and datetime.now() > scholarship.end_date:
            is_eligible = False
            reasons.append("หมดเขตการรับสมัครแล้ว")

        return is_eligible, reasons