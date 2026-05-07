"""Local development launcher — run this from the project root"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'freelancehub'))
from app import app, init_db

if __name__ == '__main__':
    init_db()
    print("FreelanceHub running on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
