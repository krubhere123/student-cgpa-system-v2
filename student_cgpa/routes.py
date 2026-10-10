from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from student_cgpa.models import CourseRecord
from student_cgpa.services.cgpa_service import CGPAService
from student_cgpa.services.validators import GradeValidator


def register_routes(app: Flask) -> None:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    USERS_FILE = DATA_DIR / "users.json"
    STUDENTS_FILE = DATA_DIR / "students.json"
    TEACHERS_FILE = DATA_DIR / "teachers.json"
    ANNOUNCEMENTS_FILE = DATA_DIR / "announcements.json"
    ASSIGNMENTS_FILE = DATA_DIR / "assignments.json"

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    def save_users(users: List[Dict[str, Any]]) -> None:
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

    def save_students(students: List[Dict[str, Any]]) -> None:
        STUDENTS_FILE.write_text(json.dumps(students, indent=2), encoding="utf-8")

    def save_teachers(teachers: List[Dict[str, Any]]) -> None:
        TEACHERS_FILE.write_text(json.dumps(teachers, indent=2), encoding="utf-8")

    def save_announcements(announcements: List[Dict[str, Any]]) -> None:
        ANNOUNCEMENTS_FILE.write_text(json.dumps(announcements, indent=2), encoding="utf-8")

    def save_assignments(assignments: List[Dict[str, Any]]) -> None:
        ASSIGNMENTS_FILE.write_text(json.dumps(assignments, indent=2), encoding="utf-8")

    def load_users() -> List[Dict[str, Any]]:
        if not USERS_FILE.exists():
            return []
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))

    def load_students() -> List[Dict[str, Any]]:
        if not STUDENTS_FILE.exists():
            return []
        return json.loads(STUDENTS_FILE.read_text(encoding="utf-8"))

    def load_teachers() -> List[Dict[str, Any]]:
        if not TEACHERS_FILE.exists():
            return []
        return json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))

    def load_announcements() -> List[Dict[str, Any]]:
        if not ANNOUNCEMENTS_FILE.exists():
            return []
        return json.loads(ANNOUNCEMENTS_FILE.read_text(encoding="utf-8"))

    def load_assignments() -> List[Dict[str, Any]]:
        if not ASSIGNMENTS_FILE.exists():
            return []
        return json.loads(ASSIGNMENTS_FILE.read_text(encoding="utf-8"))

    def ensure_seed_data() -> None:
        if not USERS_FILE.exists():
            default_users = [
                {
                    "username": "admin",
                    "password_hash": generate_password_hash("admin123"),
                    "role": "admin",
                    "name": "System Administrator",
                },
                {
                    "username": "student",
                    "password_hash": generate_password_hash("student123"),
                    "role": "student",
                    "student_id": "STD-1001",
                    "name": "Ada Johnson",
                },
                {
                    "username": "teacher",
                    "password_hash": generate_password_hash("teacher123"),
                    "role": "teacher",
                    "teacher_id": "T-1001",
                    "name": "Prof. Alice Carter",
                },
            ]
            save_users(default_users)

        if not STUDENTS_FILE.exists():
            default_students = [
                {
                    "student_id": "STD-1001",
                    "name": "Ada Johnson",
                    "records": [
                        {"course_code": "CS101", "credit_hours": 3, "grade": "A"},
                        {"course_code": "MATH201", "credit_hours": 4, "grade": "B+"},
                        {"course_code": "ENG110", "credit_hours": 2, "grade": "A-"},
                        {"course_code": "PHY150", "credit_hours": 3, "grade": "B"},
                    ],
                },
                {
                    "student_id": "STD-1002",
                    "name": "Daniel Smith",
                    "records": [
                        {"course_code": "BIO220", "credit_hours": 3, "grade": "A-"},
                        {"course_code": "CHEM101", "credit_hours": 4, "grade": "B"},
                        {"course_code": "HIST210", "credit_hours": 2, "grade": "A"},
                    ],
                },
            ]
            save_students(default_students)

        if not TEACHERS_FILE.exists():
            save_teachers([
                {
                    "teacher_id": "T-1001",
                    "name": "Prof. Alice Carter",
                    "department": "Computer Science",
                    "courses": ["CS101", "MATH201", "ENG110"],
                }
            ])

        if not ANNOUNCEMENTS_FILE.exists():
            save_announcements([
                {"id": 1, "title": "Midterm Exam Schedule", "message": "The midterm exam for CS101 will be held next Friday at 10:00 AM.", "author": "Prof. Alice Carter"},
                {"id": 2, "title": "Assignment Upload", "message": "Submit your MATH201 assignment before the end of this week.", "author": "Prof. Alice Carter"},
            ])

        if not ASSIGNMENTS_FILE.exists():
            save_assignments([
                {"id": 1, "title": "Research Summary", "course": "CS101", "due": "2026-10-18", "description": "Write a 500-word summary of your latest lecture topic."},
                {"id": 2, "title": "Problem Set 3", "course": "MATH201", "due": "2026-10-20", "description": "Complete the algebra problem set and submit in PDF format."},
            ])

    ensure_seed_data()

    def get_current_user() -> Dict[str, Any] | None:
        username = session.get("user")
        if not username:
            return None
        for user in load_users():
            if user.get("username") == username:
                return user
        return None

    def student_records_to_course_records(records: List[Dict[str, Any]]) -> List[CourseRecord]:
        return [
            CourseRecord(
                course_code=item.get("course_code", ""),
                credit_hours=int(item.get("credit_hours", 0)),
                grade=item.get("grade", ""),
            )
            for item in records
        ]

    def teacher_dashboard_data(user: Dict[str, Any]) -> Dict[str, Any]:
        teacher = next((item for item in load_teachers() if item.get("teacher_id") == user.get("teacher_id")), None)
        if teacher is None:
            teacher = {
                "teacher_id": user.get("teacher_id", "T-1001"),
                "name": user.get("name", "Teacher"),
                "department": "General",
                "courses": [],
            }

        students = load_students()
        supervise_students = []
        for student in students:
            their_courses = [
                record for record in student.get("records", [])
                if record.get("course_code") in teacher.get("courses", [])
            ]
            if their_courses:
                supervise_students.append({
                    "student_id": student.get("student_id"),
                    "name": student.get("name"),
                    "courses": their_courses,
                })

        return {
            "teacher": teacher,
            "students": supervise_students,
            "announcements": load_announcements(),
            "assignments": load_assignments(),
        }

    @app.route("/")
    def index():
        if session.get("user"):
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            users = load_users()
            user = next((u for u in users if u.get("username") == username), None)

            if user and check_password_hash(user.get("password_hash", ""), password):
                session["user"] = user["username"]
                session["role"] = user.get("role", "student")
                session["student_id"] = user.get("student_id")
                session["teacher_id"] = user.get("teacher_id")
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid username or password.", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    def dashboard():
        user = get_current_user()
        if not user:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))

        role = user.get("role", "student")
        if role == "admin":
            students = load_students()
            enriched_students = []
            for student in students:
                cgpa = CGPAService().calculate_cgpa_from_records(
                    student_records_to_course_records(student.get("records", []))
                )
                enriched_students.append({**student, "cgpa": cgpa})
            return render_template("admin.html", students=enriched_students)

        if role == "teacher":
            data = teacher_dashboard_data(user)
            return render_template("teacher_dashboard.html", **data)

        student = next((s for s in load_students() if s["student_id"] == user.get("student_id")), None)
        if not student:
            flash("Student record not found.", "error")
            return redirect(url_for("logout"))

        cgpa = CGPAService().calculate_cgpa_from_records(student_records_to_course_records(student.get("records", [])))
        announcements = load_announcements()
        assignments = load_assignments()
        return render_template("dashboard.html", student=student, cgpa=cgpa, announcements=announcements, assignments=assignments)

    @app.context_processor
    def inject_user():
        current_user = get_current_user()
        return {
            "current_user": current_user,
            "is_admin": current_user and current_user.get("role") == "admin",
            "is_teacher": current_user and current_user.get("role") == "teacher",
            "is_student": current_user and current_user.get("role") == "student",
        }
