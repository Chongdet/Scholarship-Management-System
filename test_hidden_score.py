from app import app
from models import Application, db
import json

with app.app_context():
    app_entry = Application.query.filter_by(status='interview').first()
    if app_entry:
        print(f"Found APP: {app_entry.id}")
        
        # Add a fake reason if none exists
        dummy_reason = "ผมมีความตั้งใจในการศึกษาและอยากนำความรู้ไปพัฒนาชุมชน " * 5 # ~150 chars, should give 7-8 points
        
        if app_entry.form_data:
            try:
                fd = json.loads(app_entry.form_data)
                if 'reason' not in fd or not fd['reason']:
                    fd['reason'] = dummy_reason
                    app_entry.form_data = json.dumps(fd, ensure_ascii=False)
                    db.session.commit()
                    print(f"Added dummy reason to form_data")
                else:
                    print(f"Already has reason in form: {fd['reason']}")
            except Exception as e:
                app_entry.notes = dummy_reason
                db.session.commit()
                print(f"Added dummy reason to notes. Error decoding JSON: {e}")
        else:
            app_entry.notes = dummy_reason
            db.session.commit()
            print("Added dummy reason to notes (no form_data)")
            
        print("Ready to test!")
        print("Go to /director/scoring -> click on the scholarship -> score the student with 10, 10, 10")
        print("The total should be 30 + hidden_score")
    else:
        print("No application in interview status")
