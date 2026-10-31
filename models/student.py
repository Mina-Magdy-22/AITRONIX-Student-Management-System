from abc import abstractmethod

from exceptions import EnrollmentError, NotFoundError, ValidationError

from .person import Person

POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}


def letter_grade(grade):
    for minimum, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if grade >= minimum:
            return letter
    return "F"


class Student(Person):
    STUDENT_TYPE = ""
    MIN_AGE = 15
    MAX_AGE = 70

    def __init__(self, student_id, name, age, email, major):
        super().__init__(student_id, name, age, email)
        self.major = major
        self._grades = {}

    @property
    def major(self):
        return self._major

    @major.setter
    def major(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Major cannot be empty.")
        self._major = " ".join(value.split())

    @property
    def grades(self):
        return dict(self._grades)

    @property
    def has_grades(self):
        return any(grade is not None for grade in self._grades.values())

    @property
    def gpa(self):
        graded = [grade for grade in self._grades.values() if grade is not None]
        if not graded:
            return 0.0
        return round(sum(POINTS[letter_grade(g)] for g in graded) / len(graded), 2)

    @abstractmethod
    def max_courses(self):
        pass

    @abstractmethod
    def standing(self):
        pass

    def is_enrolled(self, course_code):
        return course_code in self._grades

    def enroll(self, course_code):
        if self.is_enrolled(course_code):
            raise EnrollmentError(f"{self.name} is already enrolled in {course_code}.")
        if len(self._grades) >= self.max_courses():
            raise EnrollmentError(f"A {self.get_role()} can take at most {self.max_courses()} courses.")
        self._grades[course_code] = None

    def drop(self, course_code):
        if not self.is_enrolled(course_code):
            raise NotFoundError(f"{self.name} is not enrolled in {course_code}.")
        del self._grades[course_code]

    def set_grade(self, course_code, grade):
        if not self.is_enrolled(course_code):
            raise NotFoundError(f"{self.name} is not enrolled in {course_code}.")
        valid = isinstance(grade, (int, float)) and not isinstance(grade, bool)
        if not valid or not 0 <= grade <= 100:
            raise ValidationError("Grade must be a number between 0 and 100.")
        self._grades[course_code] = grade

    def get_details(self):
        return (
            f"ID       : {self.person_id}\n"
            f"Name     : {self.name}\n"
            f"Role     : {self.get_role()}\n"
            f"Age      : {self.age}\n"
            f"Email    : {self.email}\n"
            f"Major    : {self.major}\n"
            f"Courses  : {len(self._grades)}/{self.max_courses()}\n"
            f"GPA      : {self.gpa:.2f}\n"
            f"Standing : {self.standing()}"
        )

    def to_dict(self):
        data = super().to_dict()
        data.update(type=self.STUDENT_TYPE, major=self.major, grades=dict(self._grades))
        return data

    @staticmethod
    def from_dict(data):
        student_class = STUDENT_TYPES[data["type"]]
        extra = {"thesis": data["thesis"]} if "thesis" in data else {}
        student = student_class(data["id"], data["name"], data["age"], data["email"], data["major"], **extra)
        student._grades = dict(data.get("grades", {}))
        return student


class UndergraduateStudent(Student):
    STUDENT_TYPE = "undergraduate"

    def get_role(self):
        return "Undergraduate Student"

    def max_courses(self):
        return 6

    def standing(self):
        if not self.has_grades:
            return "No grades yet"
        return "Good Standing" if self.gpa >= 2.0 else "Academic Probation"


class GraduateStudent(Student):
    STUDENT_TYPE = "graduate"

    def __init__(self, student_id, name, age, email, major, thesis=None):
        super().__init__(student_id, name, age, email, major)
        self.thesis = thesis or "Not assigned"

    def get_role(self):
        return "Graduate Student"

    def max_courses(self):
        return 4

    def standing(self):
        if not self.has_grades:
            return "No grades yet"
        return "Good Standing" if self.gpa >= 3.0 else "Academic Probation"

    def get_details(self):
        return super().get_details() + f"\nThesis   : {self.thesis}"

    def to_dict(self):
        data = super().to_dict()
        data["thesis"] = self.thesis
        return data


STUDENT_TYPES = {"undergraduate": UndergraduateStudent, "graduate": GraduateStudent}
