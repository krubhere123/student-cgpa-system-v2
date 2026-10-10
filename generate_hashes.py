from werkzeug.security import generate_password_hash
import json

# Generate fresh password hashes
admin_hash = generate_password_hash("admin123")
student_hash = generate_password_hash("student123")
teacher_hash = generate_password_hash("teacher123")

users = [
    {
        "username": "admin",
        "password_hash": admin_hash,
        "role": "admin",
        "name": "System Administrator"
    },
    {
        "username": "student",
        "password_hash": student_hash,
        "role": "student",
        "student_id": "STD-1001",
        "name": "Ada Johnson"
    },
    {
        "username": "teacher",
        "password_hash": teacher_hash,
        "role": "teacher",
        "teacher_id": "T-1001",
        "name": "Prof. Alice Carter"
    }
]

print(json.dumps(users, indent=2))
