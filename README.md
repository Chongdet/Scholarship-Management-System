<div align="center">

# 🚀 Scholarship Management System (Flask Project)

💡 **คู่มือการติดตั้งและทำงานร่วมกันในโปรเจกต์ Flask สำหรับทีม DSSI**

**อาจารย์ที่ปรึกษา:** อ.ดร.ทศพร อเลิร์ป

</div>

---

## 🛠 Tech Stack & Framework

* **Backend Framework:** Python Flask
* **Frontend:** HTML, CSS, JavaScript (Jinja2 Templates) , tailwindcss
* **Containerization:** Docker & Docker Compose
* **Version Control:** Git & GitHub
* **Database:** SQLite, Flask-SQLAlchemy (ORM), DB Browser for SQLite

---
## 👥 Route Assignments (การแบ่งงานและผู้ดูแล)

| ชื่อ-นามสกุล | บทบาท | Route ที่รับผิดชอบ (Endpoints) | ฟังก์ชันการทำงาน |
| :--- | :--- | :--- | :--- |
| **นาย ทรงเดช จำปาเทศ** | กรรมการ | `/director/scoring`<br>`/director/ranking` | ระบบคำนวณคะแนน<br>ระบบจัดอันดับและตัดสินผล |
| **นาย กฤชณัท ศิริรังสรรค์กุล** | กรรมการ | `/director/candidates`<br>`/director/candidate/<id>` | ดูรายชื่อผู้สมัคร<br>ตรวจสอบรายละเอียดรายบุคคล |
| **นาย ยศสรัล ถิระบุตร** | เจ้าหน้าที่ | `/officer/login`<br>`/officer/scholarships` | ระบบเข้าสู่ระบบ (เจ้าหน้าที่)<br>ระบบจัดการทุนการศึกษา |
| **นาย ธีรภัทร พิกุลศรี** | เจ้าหน้าที่ | `/officer/verify`<br>`/officer/audit-log` | ตรวจสอบเอกสารการสมัคร<br>ระบบบันทึกประวัติการทำงาน (Audit Log) |
| **นาย อติวิชญ์ สีหนันท์** | เจ้าหน้าที่ | `/officer/notify`<br>`/officer/announcement` | ระบบแจ้งเตือนผลอัตโนมัติ<br>จัดการประกาศผลรอบสุดท้าย |
| **นางสาว ปัญญาพร มูลดับ** | นักศึกษา | `/student/dashboard`<br>`/student/status` | หน้าหลักของนักศึกษา<br>ระบบติดตามสถานะการสมัคร |
| **นาย กิตติพงษ์ เลี้ยงหิรัญถาวร** | นักศึกษา | `/student/login`<br>`/student/auto-match` | ระบบเข้าสู่ระบบ/ซิงค์ข้อมูล<br>ระบบจับคู่ทุนอัตโนมัติ |
| **นาย จารุวัฒน์ บุญสาร** | นักศึกษา | `/student/apply`<br>`/student/upload` | ฟอร์มสมัครทุน (Auto-Fill)<br>อัปโหลดเอกสารประกอบการสมัคร |
---

## 📂 Project Structure (โครงสร้างไฟล์)

เพื่อให้โค้ดเป็นระเบียบและดูแลรักษาง่าย เราจะแยกส่วนของ Route ออกมาไว้ในโฟลเดอร์ `routes/` (ใช้ Flask Blueprint)

```text
PROJECT_ROOT
│
├── routes/                 # 📍 โฟลเดอร์จัดการ Routes (แบ่งตามผู้รับผิดชอบ)
│   ├── director_routes.py  # ส่วนของกรรมการ (Scoring, Ranking)
│   ├── officer_routes.py   # ส่วนของเจ้าหน้าที่ (Scholarship Management, Audit Log)
│   └── student_routes.py   # ส่วนของนักศึกษา (Application Form, Status)
├── services/               # ⚙️ เซอร์วิสการประมวลผล (RegService, MatchingService ฯลฯ)
├── static/                 # 🎨 เก็บไฟล์ CSS, JS, Images และ Uploads
│   ├── css/                # สไตล์การแต่งหน้าเว็บ (Tailwind CSS ฯลฯ)
│   ├── images/             # รูปภาพประกอบระบบ
│   └── uploads/            # โฟลเดอร์สำหรับเก็บเอกสารสมัครทุนที่นักศึกษาอัปโหลด
├── templates/              # 📁 เก็บไฟล์ HTML (Jinja2) แบ่งตามผู้ใช้งาน
│   ├── director/           # หน้าเว็บส่วนของกรรมการ
│   ├── officer/            # หน้าเว็บส่วนของเจ้าหน้าที่
│   ├── student/            # หน้าเว็บส่วนของนักศึกษา
│   └── login.html, index.html # หน้าเข้าสู่ระบบและหน้าแรก
├── app.py                  # 🚀 ไฟล์เซิร์ฟเวอร์หลัก (ศูนย์กลางเชื่อมต่อ Blueprint, Database)
├── models.py               # 🗄️ โครงสร้างฐานข้อมูลตารางต่างๆ (Student, Scholarship, Application, Evaluation)
├── route_explanations.txt  # 📝 ไฟล์อธิบายการทำงาน/Data Flow ของแต่ละ Route สำหรับเตรียมพรีเซนต์
├── setup_evaluation.py     # 🔧 สคริปต์เสริมสำหรับเตรียมฐานข้อมูลคะแนน (Mock Data)
├── requirements.txt        # 📦 รายชื่อ Library ที่ต้องติดตั้ง
├── scholarship.db          # 💾 ไฟล์ฐานข้อมูล SQLite (หากลบไฟล์นี้ ระบบจะสร้างใหม่ตอนรันให้)
├── Dockerfile              # 🐳 ไฟล์ตั้งค่าการสร้าง Docker Image
└── README.md               # 📖 คู่มือการอธิบายโปรเจกต์
```
## 🚀 วิธีติดตั้งและรันโปรเจกต์ (Local Development)

การรันโปรเจกต์บนเครื่องของคุณเอง ทำตามขั้นตอนง่ายๆ ดังนี้:

### 1. การติดตั้งและรันเซิร์ฟเวอร์
**สำหรับ Windows (PowerShell/CMD):**
```bash
# 1. สร้าง Virtual Environment เพื่อแยกไลบรารี
python -m venv venv

# 2. เปิดใช้งาน Virtual Environment
.\venv\Scripts\activate

# 3. ติดตั้ง Dependencies ยืนพื้นทั้งหมด
pip install -r requirements.txt

# 4. รันโปรแกรม (เซิร์ฟเวอร์ Flask จะไปทำงานที่ http://127.0.0.1:5000)
python app.py
```
*หมายเหตุ: หากมีการปรับเปลี่ยนโค้ดระหว่างรันเซิร์ฟเวอร์ (Debug Mode = True) โปรแกรมจะ Refresh ตัวเองอัตโนมัติ*

### 🐳 Docker (Optional)
## เปิด Docker desktop เพื่อรัน
# ใช้ `docker-compose up --build เพื่อรันโปรเจค`
test
```bash
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]

```

รันแบบ container เพื่อให้ environment เหมือนกันทุกเครื่อง

Build Image

```bash
Bash
docker build -t flask-app .
```

Run Container

```bash
Bash
docker run -p 5000:5000 flask-app
```

# 🤝 Git Workflow (Team Rules)

✅ Best Practice
❌ ห้าม push เข้า main โดยตรง
✅ ใช้ Branch เสมอ
✅ ต้องสร้าง Pull Request ก่อน merge เสมอ

### 🔄 1. Update Code

ดึงโค้ดล่าสุดจาก main ก่อนเริ่มงานเสมอ

```bash
git pull origin main
```

### 🌿 2. Create Branch

สร้าง branch ใหม่สำหรับฟีเจอร์หรือการแก้ไขของคุณ

```bash
Bash
git checkout -b feature/your-name-task
```

### 📤 3. Commit & Push

บันทึกและอัปโหลดโค้ดของคุณ

```bash
git add .
git commit -m "✨ เพิ่มฟีเจอร์ [รายละเอียด]"
git push origin feature/your-name-task

```

#### 🔁 4. Pull Request

ไปที่ GitHub → เปิด New Pull Request → รอเพื่อนในทีมรีวิวและอนุมัติ



# 🚫 .gitignore

ตัวอย่างไฟล์และโฟลเดอร์ที่ไม่ควรนำเข้า Git:

```bash
venv/
__pycache__/
*.pyc
.env
.DS_Store
```

### 📝 Notes

เมื่อมีการเพิ่ม library ใหม่ในโปรเจกต์ อย่าลืมอัปเดตไฟล์ requirements.txt ด้วยคำสั่ง:

```bash
pip freeze > requirements.txt
```

<div align="center">

💙 Happy Coding with Team DSSI

👩‍💻 <i>Let's build something</i> 🚀

</div>
