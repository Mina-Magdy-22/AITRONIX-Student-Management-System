import sys

from exceptions import SchoolError, ValidationError
from models import letter_grade
from school import School


def ask(text):
    return input(text).strip()


def ask_int(text, optional=False):
    value = ask(text)
    if optional and not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError("Please enter a whole number.")


def add_student(school):
    choice = ask("Type (1 = Undergraduate, 2 = Graduate): ")
    if choice not in ("1", "2"):
        raise ValidationError("Please choose 1 or 2.")
    kind = "graduate" if choice == "2" else "undergraduate"
    name = ask("Name: ")
    age = ask_int("Age: ")
    email = ask("Email: ")
    major = ask("Major: ")
    thesis = ask("Thesis topic (optional): ") if kind == "graduate" else None
    print("Added", school.add_student(name, age, email, major, kind, thesis or None))


def list_students(school):
    if not school.students:
        print("No students yet.")
        return
    print(f"{'ID':<6}{'Name':<22}{'Type':<24}{'Major':<20}{'GPA':>5}")
    for s in school.students.values():
        print(f"{s.person_id:<6}{s.name:<22}{s.get_role():<24}{s.major:<20}{s.gpa:>5.2f}")


def search_students(school):
    results = school.search_students(ask("Search (name, major or ID): "))
    for student in results:
        print(student)
    if not results:
        print("No matches.")


def show_student(school):
    student = school.get_student(ask("Student ID: "))
    print(student.get_details())
    print("Courses:")
    for code, grade in student.grades.items():
        shown = "no grade" if grade is None else f"{grade} ({letter_grade(grade)})"
        print(f"  {school.courses[code].name:<25}{shown}")
    if not student.grades:
        print("  none")


def update_student(school):
    student_id = ask("Student ID: ")
    print("Leave a field empty to keep it.")
    student = school.update_student(
        student_id,
        name=ask("New name: "),
        age=ask_int("New age: ", optional=True),
        email=ask("New email: "),
        major=ask("New major: "),
    )
    print("Updated", student)


def delete_student(school):
    student = school.get_student(ask("Student ID: "))
    if ask(f"Delete {student.name}? (y/n): ").lower() == "y":
        school.delete_student(student.person_id)
        print("Student deleted.")


def add_teacher(school):
    name = ask("Name: ")
    age = ask_int("Age: ")
    email = ask("Email: ")
    department = ask("Department: ")
    print("Added", school.add_teacher(name, age, email, department))


def list_teachers(school):
    if not school.teachers:
        print("No teachers yet.")
        return
    for teacher in school.teachers.values():
        courses = [c.code for c in school.courses.values() if c.teacher_id == teacher.person_id]
        print(f"{teacher}  {teacher.department}  courses: {', '.join(courses) or 'none'}")


def delete_teacher(school):
    school.delete_teacher(ask("Teacher ID: "))
    print("Teacher deleted.")


def add_course(school):
    code = ask("Course code (e.g. CS101): ")
    name = ask("Course name: ")
    capacity = ask_int("Capacity (empty = 30): ", optional=True)
    print("Added", school.add_course(code, name, capacity))


def list_courses(school):
    if not school.courses:
        print("No courses yet.")
        return
    print(f"{'Code':<8}{'Name':<26}{'Seats':>7}  Teacher")
    for c in school.courses.values():
        teacher = school.teachers[c.teacher_id].name if c.teacher_id in school.teachers else "none"
        seats = f"{len(school.roster(c.code))}/{c.capacity}"
        print(f"{c.code:<8}{c.name:<26}{seats:>7}  {teacher}")


def delete_course(school):
    school.delete_course(ask("Course code: "))
    print("Course deleted.")


def assign_teacher(school):
    course = school.assign_teacher(ask("Teacher ID: "), ask("Course code: "))
    print(f"{course.code} is now assigned.")


def enroll(school):
    school.enroll(ask("Student ID: "), ask("Course code: "))
    print("Enrolled.")


def drop(school):
    school.drop(ask("Student ID: "), ask("Course code: "))
    print("Course dropped.")


def record_grade(school):
    student_id = ask("Student ID: ")
    code = ask("Course code: ")
    try:
        grade = float(ask("Grade (0-100): "))
    except ValueError:
        raise ValidationError("Please enter a number.")
    school.set_grade(student_id, code, grade)
    print("Grade saved.")


MENU = [
    ("Add student", add_student),
    ("List students", list_students),
    ("Search students", search_students),
    ("Student details", show_student),
    ("Update student", update_student),
    ("Delete student", delete_student),
    ("Add teacher", add_teacher),
    ("List teachers", list_teachers),
    ("Delete teacher", delete_teacher),
    ("Add course", add_course),
    ("List courses", list_courses),
    ("Delete course", delete_course),
    ("Assign teacher to course", assign_teacher),
    ("Enroll student in course", enroll),
    ("Drop course", drop),
    ("Record grade", record_grade),
]


def main():
    try:
        school = School()
        if "--demo" in sys.argv:
            print("Sample data loaded." if school.add_sample_data() else "Data already exists.")
        while True:
            print("\n=== Student Management System ===")
            for number, (label, _) in enumerate(MENU, start=1):
                print(f"{number:>2}. {label}")
            print(" 0. Exit")
            choice = ask("Choose: ")
            if choice == "0":
                print("Goodbye!")
                break
            if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
                print("Invalid choice.")
                continue
            try:
                MENU[int(choice) - 1][1](school)
            except SchoolError as error:
                print("Error:", error)
    except SchoolError as error:
        print("Fatal error:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
