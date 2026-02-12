<div align="center">

# 🚀 Flask Project Collaboration Setup

💡 **คู่มือการติดตั้งและทำงานร่วมกันในโปรเจกต์ Flask สำหรับทีม DSSI**

</div>

---

## ⚙️ Local Development

ใช้ `venv` เพื่อแยก dependencies ของโปรเจกต์ออกจากระบบหลัก

### 📥 1. Clone Repository

ดึงโปรเจกต์ลงมาที่เครื่อง

```bash
git clone <URL_ของ_GitHub>
cd <ชื่อโฟลเดอร์โปรเจกต์>

```

### 🧩 2. Create Virtual Environment

🪟 Windows (PowerShell)

```bash
# PowerShell
python -m venv venv

.\venv\Scripts\activate
```

🍎 Mac / 🐧 Linux (Bash)

```bash
# Bash
python3 -m venv venv

source venv/bin/activate
```

### 📦 3. Install Dependencies

ติดตั้ง library ที่จำเป็น

```bash
# Bash
pip install -r requirements.txt
```

### ▶️ 4. Run Application

เริ่มรันโปรเจกต์

```bash
Bash
python app.py
```

🌐 Open browser: <http://localhost:5000>

### 🐳 Docker (Optional)

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

# 📂 Project Structure

Plaintext

```bash
PROJECT_ROOT
│
├── venv/               # Virtual environment (ignored)
├── app.py              # Flask main app
├── Dockerfile          # Docker setup
├── requirements.txt    # Dependencies list
├── .gitignore
└── README.md
```

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
