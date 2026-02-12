from flask import Flask, render_template

app = Flask(__name__)

# บ้านนักเรียน
@app.route('/student')
def student_home():
    return render_template('student/std.html')

# บ้านเจ้าหน้าที่
@app.route('/officer')
def officer_home():
    return render_template('officer/offic.html')

# บ้านผู้อำนวยการ
@app.route('/director')
def director_home():
    return render_template('director/die.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)