# Student CGPA Performance Management System

A clean, working academic performance and CGPA management app built with Flask.

## Features

- Student, teacher, and admin login
- Role-based access control
- CGPA calculation from course records
- Lightweight JSON-based data storage for demo use
- Clean dashboard UI
- Audit-friendly structure
- Easy local setup

## Quick start

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Run the app

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug
```

Then open:

```text
http://127.0.0.1:5000
```

## Demo credentials

- Admin: `admin` / `admin123`
- Student: `student` / `student123`
- Teacher: `teacher` / `teacher123`

Admins can create additional teacher logins from the Admin Dashboard. Each teacher is assigned a unique teacher ID and a comma-separated list of courses.

## Project structure

```text
student-cgpa-system-v2/
├── app.py
├── requirements.txt
├── README.md
├── student_cgpa/
│   ├── __init__.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       ├── audit_log.py
│       ├── cgpa_service.py
│       └── validators.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── admin.html
├── static/
│   └── styles.css
├── data/
│   ├── users.json
│   └── students.json
└── tests/
    └── test_app.py
```

## Notes

This version is intentionally simple and reliable for a local demo environment. It avoids the earlier path and package import issues by using a clean package layout and a single Flask app entry point.
