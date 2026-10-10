from dataclasses import dataclass, field
from typing import List


@dataclass
class CourseRecord:
    course_code: str
    credit_hours: int
    grade: str


@dataclass
class Student:
    student_id: str
    name: str
    records: List[CourseRecord] = field(default_factory=list)
