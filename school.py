import json
from pathlib import Path

from exceptions import DuplicateError, EnrollmentError, NotFoundError, SchoolError, ValidationError
from models import STUDENT_TYPES, Course, Student, Teacher


class School:
    def __init__(self, filename="data/school.json"):
        self.filename = Path(filename)
        self.students = {}
        self.teachers = {}
        self.courses = {}
        self.load()

    def load(self):
        if not self.filename.exists():
            return
        try:
            data = json.loads(self.filename.read_text(encoding="utf-8"))
            self.courses = {c["code"]: Course.from_dict(c) for c in data["courses"]}
            self.teachers = {t["id"]: Teacher.from_dict(t) for t in data["teachers"]}
            self.students = {s["id"]: Student.from_dict(s) for s in data["students"]}
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise SchoolError(f"Could not read {self.filename}: {error}") from error

    def save(self):
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "students": [s.to_dict() for s in self.students.values()],
            "teachers": [t.to_dict() for t in self.teachers.values()],
            "courses": [c.to_dict() for c in self.courses.values()],
        }
        self.filename.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _next_id(prefix, items):
        numbers = [int(key[len(prefix):]) for key in items]
        return f"{prefix}{max(numbers, default=0) + 1:03d}"

    @staticmethod
    def _check_email(email, people, ignore_id=None):
        email = str(email).strip().lower()
        for person in people.values():
            if person.email == email and person.person_id != ignore_id:
                raise DuplicateError(f"The email {email} is already used.")

    def get_student(self, student_id):
        key = str(student_id).strip().upper()
        if key not in self.students:
            raise NotFoundError(f"No student with ID {key}.")
        return self.students[key]

    def get_teacher(self, teacher_id):
        key = str(teacher_id).strip().upper()
        if key not in self.teachers:
            raise NotFoundError(f"No teacher with ID {key}.")
        return self.teachers[key]

    def get_course(self, code):
        key = str(code).strip().upper()
        if key not in self.courses:
            raise NotFoundError(f"No course with code {key}.")
        return self.courses[key]

    def add_student(self, name, age, email, major, kind="undergraduate", thesis=None):
        student_class = STUDENT_TYPES.get(kind)
        if student_class is None:
            raise ValidationError("Student type must be undergraduate or graduate.")
        self._check_email(email, self.students)
        extra = {"thesis": thesis} if kind == "graduate" and thesis else {}
        student = student_class(self._next_id("S", self.students), name, age, email, major, **extra)
        self.students[student.person_id] = student
        self.save()
        return student

    def update_student(self, student_id, name=None, age=None, email=None, major=None):
        student = self.get_student(student_id)
        if email:
            self._check_email(email, self.students, student.person_id)
        old = (student.name, student.age, student.email, student.major)
        try:
            if name:
                student.name = name
            if age is not None:
                student.age = age
            if email:
                student.email = email
            if major:
                student.major = major
        except ValidationError:
            student.name, student.age, student.email, student.major = old
            raise
        self.save()
        return student

    def delete_student(self, student_id):
        student = self.get_student(student_id)
        del self.students[student.person_id]
        self.save()

    def search_students(self, keyword):
        keyword = keyword.strip().lower()
        return [
            s for s in self.students.values()
            if keyword in s.name.lower() or keyword in s.major.lower() or keyword == s.person_id.lower()
        ]

    def add_teacher(self, name, age, email, department):
        self._check_email(email, self.teachers)
        teacher = Teacher(self._next_id("T", self.teachers), name, age, email, department)
        self.teachers[teacher.person_id] = teacher
        self.save()
        return teacher

    def delete_teacher(self, teacher_id):
        teacher = self.get_teacher(teacher_id)
        for course in self.courses.values():
            if course.teacher_id == teacher.person_id:
                course.teacher_id = None
        del self.teachers[teacher.person_id]
        self.save()

    def add_course(self, code, name, capacity=None):
        course = Course(code, name, 30 if capacity is None else capacity)
        if course.code in self.courses:
            raise DuplicateError(f"Course {course.code} already exists.")
        self.courses[course.code] = course
        self.save()
        return course

    def delete_course(self, code):
        course = self.get_course(code)
        if self.roster(course.code):
            raise EnrollmentError(f"{course.code} still has enrolled students.")
        del self.courses[course.code]
        self.save()

    def assign_teacher(self, teacher_id, code):
        course = self.get_course(code)
        course.teacher_id = self.get_teacher(teacher_id).person_id if teacher_id else None
        self.save()
        return course

    def roster(self, code):
        return [s for s in self.students.values() if s.is_enrolled(code)]

    def enroll(self, student_id, code):
        student = self.get_student(student_id)
        course = self.get_course(code)
        if len(self.roster(course.code)) >= course.capacity:
            raise EnrollmentError(f"{course.code} is full ({course.capacity} seats).")
        student.enroll(course.code)
        self.save()

    def drop(self, student_id, code):
        self.get_student(student_id).drop(self.get_course(code).code)
        self.save()

    def set_grade(self, student_id, code, grade):
        self.get_student(student_id).set_grade(self.get_course(code).code, grade)
        self.save()

    def add_sample_data(self):
        if self.students or self.teachers or self.courses:
            return False
        courses = [("CS101", "Intro to Programming", 30), ("CS201", "Data Structures", 25),
                   ("MA101", "Calculus I", 40), ("PH101", "Physics I", 35)]
        for code, name, capacity in courses:
            self.add_course(code, name, capacity)
        ahmed = self.add_teacher("Ahmed Hassan", 45, "ahmed@school.edu", "Computer Science")
        mona = self.add_teacher("Mona Ali", 38, "mona@school.edu", "Mathematics")
        self.assign_teacher(ahmed.person_id, "CS101")
        self.assign_teacher(ahmed.person_id, "CS201")
        self.assign_teacher(mona.person_id, "MA101")
        sara = self.add_student("Sara Mohamed", 20, "sara@student.edu", "Computer Science")
        omar = self.add_student("Omar Khaled", 21, "omar@student.edu", "Mathematics")
        laila = self.add_student("Laila Samir", 24, "laila@student.edu", "Computer Science",
                                 "graduate", "Machine Learning in Education")
        grades = [(sara, "CS101", 92), (sara, "MA101", 85), (omar, "MA101", 58),
                  (omar, "PH101", 71), (laila, "CS201", 95)]
        for student, code, grade in grades:
            self.enroll(student.person_id, code)
            self.set_grade(student.person_id, code, grade)
        return True
