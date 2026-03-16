# -*- coding: utf-8 -*-
"""
บริการส่งอีเมลแจ้งเตือนนักศึกษา
รองรับ: Mailtrap Email API (ส่งจริง), SMTP (Gmail, Sandbox ฯลฯ)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
except ImportError:
    requests = None


def send_reject_notification(to_email: str, student_name: str, scholarship_name: str, reject_reason: str) -> bool:
    """
    ส่งอีเมลแจ้งเตือนเมื่อใบสมัครถูกส่งกลับให้แก้ไข/ปฏิเสธ
    
    Args:
        to_email: อีเมลนักศึกษา
        student_name: ชื่อนักศึกษา
        scholarship_name: ชื่อทุนที่สมัคร
        reject_reason: เหตุผลที่ส่งกลับ/ปฏิเสธ
    
    Returns:
        True ถ้าส่งสำเร็จ, False ถ้าส่งไม่สำเร็จ
    """
    # ถ้าตั้ง EMAIL_OVERRIDE ให้ส่งไปที่อีเมลนั้นแทน (ใช้ทดสอบ)
    override = os.getenv("EMAIL_OVERRIDE", "").strip()
    if override and "@" in override:
        to_email = override

    if not to_email or "@" not in to_email:
        return False

    from_email = os.getenv("SYSTEM_EMAIL", "ubustudent.d@ubu.ac.th").strip()
    if not from_email or "@" not in from_email:
        from_email = "ubustudent.d@ubu.ac.th"

    subject = f"แจ้งเตือน: ใบสมัครทุน {scholarship_name} - ต้องแก้ไข"
    body = f"""
สวัสดีคุณ {student_name}

ระบบทุนการศึกษา มหาวิทยาลัยอุบลราชธานี แจ้งว่า ใบสมัครทุน "{scholarship_name}" ของคุณถูกส่งกลับเพื่อแก้ไข

เหตุผล:
{reject_reason}

กรุณาเข้าสู่ระบบเพื่อตรวจสอบและแก้ไขเอกสารให้ครบถ้วน
https://scholarship.ubu.ac.th (หรือ URL ของระบบ)

หากมีคำถาม กรุณาติดต่อสำนักงานพัฒนานักศึกษา
Email: ubustudent.d@ubu.ac.th
โทร: 045-353000 ต่อ 1210

สำนักงานพัฒนานักศึกษา
มหาวิทยาลัยอุบลราชธานี
""".strip()

    # --- Mailtrap Email API (ส่งอีเมลจริงไปที่ผู้รับ) ---
    api_token = os.getenv("MAILTRAP_API_TOKEN", "").strip()
    debug = os.getenv("DEBUG_EMAIL", "").lower() in ("1", "true", "yes")
    if api_token and requests:
        try:
            resp = requests.post(
                "https://send.api.mailtrap.io/api/send",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": {"email": from_email, "name": "สำนักงานพัฒนานักศึกษา"},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "text": body,
                },
                timeout=10,
            )
            ok = 200 <= resp.status_code < 300
            if debug or not ok:
                try:
                    err_body = resp.text[:500] if resp.text else "(empty)"
                    print(f"[EMAIL] API status={resp.status_code} ok={ok} body={err_body}")
                except Exception:
                    pass
            return ok
        except Exception as e:
            if debug:
                print(f"[EMAIL] API error: {e}")
            return False

    # --- SMTP (Sandbox, Gmail ฯลฯ) ---
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

    if not smtp_user or not smtp_pass:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"สำนักงานพัฒนานักศึกษา <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        if debug:
            print(f"[EMAIL] SMTP error: {e}")
        return False


def send_interview_notification(
    to_email: str, 
    student_name: str, 
    scholarship_name: str,
    interview_date: str = None,
    interview_time: str = None,
    interview_location: str = None
) -> bool:
    """
    ส่งอีเมลแจ้งเตือนเมื่อใบสมัครผ่านการตรวจเอกสารและอนุมัตินัดสัมภาษณ์แล้ว
    """
    override = os.getenv("EMAIL_OVERRIDE", "").strip()
    if override and "@" in override:
        to_email = override

    if not to_email or "@" not in to_email:
        return False

    from_email = os.getenv("SYSTEM_EMAIL", "ubustudent.d@ubu.ac.th").strip()
    if not from_email or "@" not in from_email:
        from_email = "ubustudent.d@ubu.ac.th"

    subject = f"แจ้งเตือน: ใบสมัครทุน {scholarship_name} - ผ่านการตรวจเอกสาร/นัดสัมภาษณ์"
    
    details_section = ""
    if interview_date or interview_time or interview_location:
        details_section = "\nรายละเอียดการสัมภาษณ์:\n"
        if interview_date:
            details_section += f"- วันที่: {interview_date}\n"
        if interview_time:
            details_section += f"- เวลา: {interview_time}\n"
        if interview_location:
            details_section += f"- สถานที่: {interview_location}\n"

    body = f"""
สวัสดีคุณ {student_name}

ระบบทุนการศึกษา มหาวิทยาลัยอุบลราชธานี แจ้งว่า ใบสมัครทุน "{scholarship_name}" ของคุณผ่านการตรวจเอกสารและได้รับการอนุมัติให้นัดสัมภาษณ์แล้ว
{details_section}
กรุณาติดตามกำหนดการสัมภาษณ์ผ่านระบบหรือประกาศของคณะ/หน่วยงานที่เกี่ยวข้อง
https://scholarship.ubu.ac.th (หรือ URL ของระบบ)


หากมีคำถาม กรุณาติดต่อสำนักงานพัฒนานักศึกษา
Email: ubustudent.d@ubu.ac.th
โทร: 045-353000 ต่อ 1210

สำนักงานพัฒนานักศึกษา
มหาวิทยาลัยอุบลราชธานี
""".strip()

    api_token = os.getenv("MAILTRAP_API_TOKEN", "").strip()
    debug = os.getenv("DEBUG_EMAIL", "").lower() in ("1", "true", "yes")
    if api_token and requests:
        try:
            resp = requests.post(
                "https://send.api.mailtrap.io/api/send",
                headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
                json={
                    "from": {"email": from_email, "name": "สำนักงานพัฒนานักศึกษา"},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "text": body,
                },
                timeout=10,
            )
            ok = 200 <= resp.status_code < 300
            if debug or not ok:
                try:
                    print(f"[EMAIL] Interview API status={resp.status_code} ok={ok}")
                except Exception:
                    pass
            return ok
        except Exception as e:
            if debug:
                print(f"[EMAIL] Interview API error: {e}")
            return False

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "").replace(" ", "")
    if not smtp_user or not smtp_pass:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"สำนักงานพัฒนานักศึกษา <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        if debug:
            print(f"[EMAIL] Interview SMTP error: {e}")
        return False


def send_announcement_notification(
    to_email: str, student_name: str, scholarship_name: str, announcement_date: str, is_awarded: bool = False
) -> bool:
    """
    ส่งอีเมลแจ้งเตือนเมื่อกำหนดวันที่ประกาศทุน
    ส่งให้นักศึกษาทุกคนที่สมัครทุนนี้ (แจ้งผลได้/ไม่ได้)
    """
    override = os.getenv("EMAIL_OVERRIDE", "").strip()
    if override and "@" in override:
        to_email = override

    if not to_email or "@" not in to_email:
        return False

    from_email = os.getenv("SYSTEM_EMAIL", "ubustudent.d@ubu.ac.th").strip()
    if not from_email or "@" not in from_email:
        from_email = "ubustudent.d@ubu.ac.th"

    if is_awarded:
        subject = f"ขอแสดงความยินดี: คุณได้รับทุน {scholarship_name}"
        status_text = "<h2 style='color: #28a745; margin: 0;'>🎉 ขอแสดงความยินดี! คุณได้รับทุนการศึกษา</h2>"
        desc_text = f"<p style='font-size: 16px;'>ระบบตกลงพิจารณาให้คุณเป็นผู้ได้รับทุน <strong>{scholarship_name}</strong></p>"
    else:
        subject = f"แจ้งผลการพิจารณาทุน {scholarship_name}"
        status_text = "<h2 style='color: #dc3545; margin: 0;'>ผลการพิจารณาทุนการศึกษา</h2>"
        desc_text = f"<p style='font-size: 16px;'>ขอแสดงความเสียใจ คุณไม่ผ่านการพิจารณาสำหรับรับทุน <strong>{scholarship_name}</strong> ในครั้งนี้</p>"

    body = f"""
    <html>
    <body style="font-family: 'Sarabun', Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f4f6f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 5px solid {'#28a745' if is_awarded else '#dc3545'};">
            
            <div style="text-align: center; margin-bottom: 25px;">
                {status_text}
            </div>

            <p style="font-size: 16px;">เรียน คุณ <strong>{student_name}</strong>,</p>
            {desc_text}
            
            <div style="background-color: #f8f9fa; border-left: 4px solid #0056b3; padding: 15px 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0 0 10px 0; font-size: 15px; color: #555;">วันที่ประกาศผลอ้างอิง: <strong>{announcement_date}</strong></p>
                <p style="margin: 0; font-size: 15px;">กรุณาเข้าสู่ระบบเพื่อตรวจสอบรายละเอียดเพิ่มเติม ปริ้นเอกสาร หรือดำเนินการในขั้นตอนต่อไป</p>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="https://scholarship.ubu.ac.th" style="display: inline-block; padding: 12px 25px; background-color: #0056b3; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">เข้าสู่ระบบจัดการทุน</a>
                </div>
            </div>

            <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;" />
            
            <div style="font-size: 14px; color: #777;">
                <p style="margin: 0 0 5px 0;">หากมีข้อสงสัยเพิ่มเติม กรุณาติดต่อ:</p>
                <p style="margin: 0 0 15px 0;">
                    <strong>สำนักงานพัฒนานักศึกษา มหาวิทยาลัยอุบลราชธานี</strong><br>
                    📧 Email: <a href="mailto:ubustudent.d@ubu.ac.th" style="color: #0056b3;">ubustudent.d@ubu.ac.th</a><br>
                    📞 โทร: 045-353000 ต่อ 1210
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    api_token = os.getenv("MAILTRAP_API_TOKEN", "").strip()
    debug = os.getenv("DEBUG_EMAIL", "").lower() in ("1", "true", "yes")
    if api_token and requests:
        try:
            resp = requests.post(
                "https://send.api.mailtrap.io/api/send",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": {"email": from_email, "name": "สำนักงานพัฒนานักศึกษา"},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "html": body,
                },
                timeout=10,
            )
            ok = 200 <= resp.status_code < 300
            if debug or not ok:
                try:
                    print(f"[EMAIL] Announcement API status={resp.status_code} ok={ok}")
                except Exception:
                    pass
            return ok
        except Exception as e:
            if debug:
                print(f"[EMAIL] Announcement API error: {e}")
            return False

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

    if not smtp_user or not smtp_pass:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"สำนักงานพัฒนานักศึกษา <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        if debug:
            print(f"[EMAIL] Announcement SMTP error: {e}")
        return False
