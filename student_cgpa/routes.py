from __future__ import annotations

import json
import csv
import io
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
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

        # Add the demo teacher to older user files created before teacher login
        # was introduced. Do not replace or rewrite existing credentials.
        existing_users = load_users()
        if not any(user.get("role") == "teacher" for user in existing_users):
            existing_users.append({
                "username": "teacher",
                "password_hash": generate_password_hash("teacher123"),
                "role": "teacher",
                "teacher_id": "T-1001",
                "name": "Prof. Alice Carter",
            })
            save_users(existing_users)

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
                records = student.get("records", [])
                cgpa = CGPAService().calculate_cgpa_from_records(student_records_to_course_records(records)) if records else 0.0
                enriched_students.append({**student, "cgpa": cgpa})
            query = request.args.get("q", "").strip().casefold()
            visible_students = [s for s in enriched_students if query in s.get("name", "").casefold() or query in s.get("student_id", "").casefold()]
            return render_template("admin.html", students=visible_students, total_students=len(enriched_students), teachers=load_teachers(), query=query)

        if role == "teacher":
            data = teacher_dashboard_data(user)
            return render_template("teacher_dashboard.html", **data)

        student = next((s for s in load_students() if s["student_id"] == user.get("student_id")), None)
        if not student:
            flash("Student record not found.", "error")
            return redirect(url_for("logout"))

        records = student.get("records", [])
        cgpa = CGPAService().calculate_cgpa_from_records(student_records_to_course_records(records)) if records else 0.0
        announcements = load_announcements()
        assignments = load_assignments()
        status = "Good Standing" if cgpa >= 3.0 else "At Risk"
        return render_template("dashboard.html", student=student, cgpa=cgpa, status=status, announcements=announcements, assignments=assignments)

    def require_role(role: str):
        user = get_current_user()
        if not user or user.get("role") != role:
            flash("You are not authorized to perform this action.", "error")
            return None
        return user

    @app.route("/admin/students", methods=["POST"])
    def add_student():
        if not require_role("admin"):
            return redirect(url_for("login"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        users, students = load_users(), load_students()
        if not all((username, password, student_id, name)):
            flash("Complete all student account fields.", "error")
        elif any(u.get("username", "").casefold() == username.casefold() for u in users):
            flash("That username is already in use.", "error")
        elif any(s.get("student_id", "").casefold() == student_id.casefold() for s in students):
            flash("That student ID already exists.", "error")
        else:
            users.append({"username": username, "password_hash": generate_password_hash(password), "role": "student", "student_id": student_id, "name": name})
            students.append({"student_id": student_id, "name": name, "records": []})
            save_users(users)
            save_students(students)
            flash("Student account created. Add course records from the student list.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/admin/students.csv")
    def export_students():
        if not require_role("admin"):
            return redirect(url_for("login"))
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Name", "Course", "Credits", "Grade", "CGPA"])
        for student in load_students():
            records = student.get("records", [])
            cgpa = CGPAService().calculate_cgpa_from_records(student_records_to_course_records(records)) if records else 0.0
            if records:
                for record in records:
                    writer.writerow([student.get("student_id", ""), student.get("name", ""), record.get("course_code", ""), record.get("credit_hours", ""), record.get("grade", ""), f"{cgpa:.4f}"])
            else:
                writer.writerow([student.get("student_id", ""), student.get("name", ""), "", "", "", f"{cgpa:.4f}"])
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=student-performance.csv"})

    @app.route("/admin/students/<student_id>", methods=["GET", "POST"])
    def student_detail(student_id: str):
        if not require_role("admin"):
            return redirect(url_for("login"))
        students = load_students()
        student = next((s for s in students if s.get("student_id") == student_id), None)
        if not student:
            flash("Student record not found.", "error")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Student name cannot be empty.", "error")
            else:
                student["name"] = name
                save_students(students)
                users = load_users()
                for account in users:
                    if account.get("student_id") == student_id:
                        account["name"] = name
                save_users(users)
                flash("Student details updated.", "success")
            return redirect(url_for("student_detail", student_id=student_id))
        records = student.get("records", [])
        cgpa = CGPAService().calculate_cgpa_from_records(student_records_to_course_records(records)) if records else 0.0
        return render_template("student_detail.html", student=student, cgpa=cgpa, status="Good Standing" if cgpa >= 3.0 else "At Risk")

    @app.route("/admin/students/<student_id>/records", methods=["POST"])
    def add_student_record(student_id: str):
        if not require_role("admin"):
            return redirect(url_for("login"))
        students = load_students()
        student = next((s for s in students if s.get("student_id") == student_id), None)
        course_code = request.form.get("course_code", "").strip().upper()
        try:
            raw_credit_hours = request.form.get("credit_hours", "").strip()
            if not raw_credit_hours.isdigit():
                raise ValueError("Credit hours must be a whole number.")
            credit_hours = GradeValidator.validate_credit_hours(int(raw_credit_hours))
            grade = GradeValidator.validate_grade(request.form.get("grade", ""))
            if not course_code or len(course_code) > 20:
                raise ValueError("Enter a valid course code.")
            if not student:
                raise ValueError("Student record not found.")
            if any(r.get("course_code", "").casefold() == course_code.casefold() for r in student.get("records", [])):
                raise ValueError("That course is already recorded for this student.")
            student.setdefault("records", []).append({"course_code": course_code, "credit_hours": credit_hours, "grade": grade})
            save_students(students)
            flash("Course record added.", "success")
        except (TypeError, ValueError) as error:
            flash(str(error) or "Enter valid course details.", "error")
        return redirect(url_for("student_detail", student_id=student_id))

    @app.route("/admin/students/<student_id>/records/<course_code>/delete", methods=["POST"])
    def delete_student_record(student_id: str, course_code: str):
        if not require_role("admin"):
            return redirect(url_for("login"))
        students = load_students()
        student = next((s for s in students if s.get("student_id") == student_id), None)
        if student:
            records = student.get("records", [])
            student["records"] = [record for record in records if record.get("course_code") != course_code]
            if len(records) == len(student["records"]):
                flash("Course record not found.", "error")
            else:
                save_students(students)
                flash("Course record removed.", "success")
        return redirect(url_for("student_detail", student_id=student_id))

    @app.route("/admin/students/<student_id>/delete", methods=["POST"])
    def delete_student(student_id: str):
        if not require_role("admin"):
            return redirect(url_for("login"))
        students = load_students()
        if not any(s.get("student_id") == student_id for s in students):
            flash("Student record not found.", "error")
            return redirect(url_for("dashboard"))
        save_students([s for s in students if s.get("student_id") != student_id])
        save_users([u for u in load_users() if not (u.get("role") == "student" and u.get("student_id") == student_id)])
        flash("Student and associated login deleted.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/admin/teachers", methods=["POST"])
    def add_teacher():
        if not require_role("admin"):
            return redirect(url_for("login"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        teacher_id = request.form.get("teacher_id", "").strip()
        department = request.form.get("department", "").strip()
        courses = list(dict.fromkeys(c.strip().upper() for c in request.form.get("courses", "").split(",") if c.strip()))
        users, teachers = load_users(), load_teachers()
        if not all((username, password, name, teacher_id, department)):
            flash("Complete all teacher fields.", "error")
        elif any(u.get("username", "").casefold() == username.casefold() for u in users):
            flash("That username is already in use.", "error")
        elif any(t.get("teacher_id") == teacher_id for t in teachers):
            flash("That teacher ID already exists.", "error")
        else:
            users.append({"username": username, "password_hash": generate_password_hash(password), "role": "teacher", "teacher_id": teacher_id, "name": name})
            teachers.append({"teacher_id": teacher_id, "name": name, "department": department, "courses": courses})
            save_users(users)
            save_teachers(teachers)
            flash("Teacher login created.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/teacher/announcements", methods=["POST"])
    def add_announcement():
        user = require_role("teacher")
        if not user:
            return redirect(url_for("login"))
        title, message = request.form.get("title", "").strip(), request.form.get("message", "").strip()
        if title and message:
            items = load_announcements()
            items.append({"id": max((x.get("id", 0) for x in items), default=0) + 1, "title": title, "message": message, "author": user.get("name", user["username"])})
            save_announcements(items)
            flash("Announcement published.", "success")
        else:
            flash("Enter an announcement title and message.", "error")
        return redirect(url_for("dashboard"))

    @app.route("/teacher/assignments", methods=["POST"])
    def add_assignment():
        user = require_role("teacher")
        if not user:
            return redirect(url_for("login"))
        title, course = request.form.get("title", "").strip(), request.form.get("course", "").strip().upper()
        teacher = next((t for t in load_teachers() if t.get("teacher_id") == user.get("teacher_id")), {})
        if title and course in teacher.get("courses", []) and request.form.get("due") and request.form.get("description", "").strip():
            items = load_assignments()
            items.append({"id": max((x.get("id", 0) for x in items), default=0) + 1, "title": title, "course": course, "due": request.form["due"], "description": request.form["description"].strip()})
            save_assignments(items)
            flash("Assignment created.", "success")
        else:
            flash("Enter assignment details for one of your assigned courses.", "error")
        return redirect(url_for("dashboard"))

    @app.route("/teacher/grades/<student_id>/<course_code>", methods=["POST"])
    def update_teacher_grade(student_id: str, course_code: str):
        user = require_role("teacher")
        if not user:
            return redirect(url_for("login"))
        teacher = next((t for t in load_teachers() if t.get("teacher_id") == user.get("teacher_id")), {})
        if course_code not in teacher.get("courses", []):
            flash("You are not assigned to that course.", "error")
            return redirect(url_for("dashboard"))
        try:
            grade = GradeValidator.validate_grade(request.form.get("grade", ""))
        except ValueError:
            flash("Select a valid grade.", "error")
            return redirect(url_for("dashboard"))
        students = load_students()
        student = next((s for s in students if s.get("student_id") == student_id), None)
        record = next((r for r in student.get("records", []) if r.get("course_code") == course_code), None) if student else None
        if not record:
            flash("Student course record not found.", "error")
        else:
            record["grade"] = grade
            save_students(students)
            flash("Grade updated.", "success")
        return redirect(url_for("dashboard"))

    @app.context_processor
    def inject_user():
        current_user = get_current_user()
        return {
            "current_user": current_user,
            "is_admin": current_user and current_user.get("role") == "admin",
            "is_teacher": current_user and current_user.get("role") == "teacher",
            "is_student": current_user and current_user.get("role") == "student",
        }
