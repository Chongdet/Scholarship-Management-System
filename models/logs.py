from . import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    user_name = db.Column(db.String(100), nullable=False) # ชื่อผู้ใช้งาน (กรรมการ/เจ้าหน้าที่)
    action = db.Column(db.String(100), nullable=False)    # ชนิดกิจกรรม
    action_title = db.Column(db.String(100))             # ชื่อกิจกรรมภาษาไทย
    details = db.Column(db.Text)                         # รายละเอียด
    ip_address = db.Column(db.String(45))                # เลข IP ผู้ใช้งาน

    def __init__(self, user_name, action, details, ip_address, action_title=None):
        self.user_name = user_name
        self.action = action
        self.details = details
        self.ip_address = ip_address
        self.action_title = action_title