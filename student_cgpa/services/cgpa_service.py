from typing import List

from student_cgpa.models import CourseRecord
from student_cgpa.services.audit_log import AuditLogger
from student_cgpa.services.validators import GradeValidator

GRADE_POINTS = {
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
}


class CGPAService:
    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit_logger = audit_logger or AuditLogger()

    def calculate_cgpa(self, student) -> float:
        if not student.records:
            raise ValueError("Student has no recorded courses")
        return self.calculate_cgpa_from_records(student.records)

    def calculate_cgpa_from_records(self, records: List[CourseRecord]) -> float:
        if not records:
            raise ValueError("Student has no recorded courses")

        total_weighted_points = 0.0
        total_credit_hours = 0

        for record in records:
            grade = GradeValidator.validate_grade(record.grade)
            credit_hours = GradeValidator.validate_credit_hours(record.credit_hours)
            total_weighted_points += GRADE_POINTS[grade] * credit_hours
            total_credit_hours += credit_hours

        cgpa = total_weighted_points / total_credit_hours
        self.audit_logger.log_event(
            action="calculate_cgpa",
            actor="system",
            details={"total_credit_hours": total_credit_hours, "cgpa": round(cgpa, 4)},
        )
        return round(cgpa, 4)
