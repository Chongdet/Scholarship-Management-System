# -*- coding: utf-8 -*-
"""สคริปต์ทดสอบการส่งอีเมล - ใช้ตรวจหาสาเหตุที่อีเมลไม่ส่ง"""
import sys
import os

# โหลด .env จากโฟลเดอร์โปรเจกต์
import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / ".env"
loaded = load_dotenv(env_path, override=True)

def main():
    from services.email_service import send_reject_notification, send_announcement_notification

    to = os.getenv("EMAIL_OVERRIDE") or "teeraphat.pi.68@ubu.ac.th"
    is_announce = len(sys.argv) > 1 and sys.argv[1].lower() in ("announce", "ประกาศ", "2")

    print("=" * 50)
    print("ทดสอบส่งอีเมล: " + ("ประกาศทุน" if is_announce else "ส่งกลับให้แก้ไข"))
    print(f"  ไปที่: {to}")
    print("=" * 50)

    if is_announce:
        ok = send_announcement_notification(
            to_email=to,
            student_name="นักศึกษาทดสอบ",
            scholarship_name="ทุนทดสอบ",
            announcement_date="04/03/2026",
        )
    else:
        ok = send_reject_notification(
            to_email=to,
            student_name="นักศึกษาทดสอบ",
            scholarship_name="ทุนทดสอบ",
            reject_reason="เหตุผลทดสอบจาก test_email.py",
        )

    print(f"ผลลัพธ์: {'ส่งสำเร็จ' if ok else 'ส่งไม่สำเร็จ'}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
