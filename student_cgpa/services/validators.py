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


class GradeValidator:
    @staticmethod
    def validate_grade(grade: str) -> str:
        normalized = grade.strip().upper()
        if normalized not in GRADE_POINTS:
            raise ValueError(f"Unsupported grade: {grade}")
        return normalized

    @staticmethod
    def validate_credit_hours(credit_hours: int) -> int:
        if not isinstance(credit_hours, int) or credit_hours <= 0:
            raise ValueError("Credit hours must be a positive integer")
        return credit_hours
