import tempfile
import unittest
from pathlib import Path

from exceptions import DuplicateError, EnrollmentError, NotFoundError, ValidationError
from models import GraduateStudent, Person, UndergraduateStudent
from school import School


class ModelTests(unittest.TestCase):
    def test_person_is_abstract(self):
        with self.assertRaises(TypeError):
            Person("X1", "Name", 20, "a@b.com")

    def test_validation(self):
        with self.assertRaises(ValidationError):
            UndergraduateStudent("S001", "Sara", 5, "s@x.com", "CS")
        student = UndergraduateStudent("S001", "Sara", 20, "s@x.com", "CS")
        with self.assertRaises(ValidationError):
            student.email = "wrong"
        with self.assertRaises(ValidationError):
            student.name = "R2D2"

    def test_polymorphism(self):
        under = UndergraduateStudent("S001", "Sara", 20, "s@x.com", "CS")
        grad = GraduateStudent("S002", "Laila", 24, "l@x.com", "CS")
        self.assertEqual((under.max_courses(), grad.max_courses()), (6, 4))
        self.assertEqual(under.get_role(), "Undergraduate Student")
        self.assertIn("Thesis", grad.get_details())
        self.assertNotIn("Thesis", under.get_details())

    def test_enroll_limit_and_drop(self):
        grad = GraduateStudent("S001", "Laila", 24, "l@x.com", "CS")
        for code in ("A1", "A2", "A3", "A4"):
            grad.enroll(code)
        with self.assertRaises(EnrollmentError):
            grad.enroll("A5")
        with self.assertRaises(EnrollmentError):
            grad.enroll("A1")
        grad.drop("A4")
        with self.assertRaises(NotFoundError):
            grad.drop("A4")

    def test_gpa_and_standing(self):
        student = UndergraduateStudent("S001", "Sara", 20, "s@x.com", "CS")
        student.enroll("CS101")
        student.enroll("MA101")
        self.assertEqual(student.standing(), "No grades yet")
        student.set_grade("CS101", 95)
        student.set_grade("MA101", 65)
        self.assertEqual(student.gpa, 2.5)
        self.assertEqual(student.standing(), "Good Standing")
        with self.assertRaises(ValidationError):
            student.set_grade("CS101", 101)


class SchoolTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "school.json"
        self.school = School(self.path)

    def test_student_crud_and_search(self):
        student = self.school.add_student("Sara", 20, "s@x.com", "CS")
        self.assertEqual(student.person_id, "S001")
        with self.assertRaises(DuplicateError):
            self.school.add_student("Other", 21, "S@X.com", "CS")
        self.school.update_student("s001", name="Sara Ali", age=21)
        self.assertEqual(self.school.get_student("S001").name, "Sara Ali")
        self.assertEqual(len(self.school.search_students("ali")), 1)
        self.school.delete_student("S001")
        with self.assertRaises(NotFoundError):
            self.school.get_student("S001")

    def test_failed_update_keeps_old_values(self):
        self.school.add_student("Sara", 20, "s@x.com", "CS")
        with self.assertRaises(ValidationError):
            self.school.update_student("S001", name="New Name", age=3)
        self.assertEqual(self.school.get_student("S001").name, "Sara")

    def test_course_full_and_delete_rules(self):
        self.school.add_course("CS101", "Intro", capacity=1)
        a = self.school.add_student("Sara", 20, "a@x.com", "CS")
        b = self.school.add_student("Omar", 21, "b@x.com", "CS")
        self.school.enroll(a.person_id, "cs101")
        with self.assertRaises(EnrollmentError):
            self.school.enroll(b.person_id, "CS101")
        with self.assertRaises(EnrollmentError):
            self.school.delete_course("CS101")
        self.school.drop(a.person_id, "CS101")
        self.school.delete_course("CS101")

    def test_deleting_teacher_unassigns_courses(self):
        self.school.add_course("CS101", "Intro")
        teacher = self.school.add_teacher("Ahmed", 40, "t@x.com", "CS")
        self.school.assign_teacher(teacher.person_id, "CS101")
        self.school.delete_teacher(teacher.person_id)
        self.assertIsNone(self.school.get_course("CS101").teacher_id)

    def test_data_is_saved_and_loaded(self):
        self.assertTrue(self.school.add_sample_data())
        self.assertFalse(self.school.add_sample_data())
        reloaded = School(self.path)
        laila = reloaded.get_student("S003")
        self.assertIsInstance(laila, GraduateStudent)
        self.assertEqual(laila.thesis, "Machine Learning in Education")
        self.assertEqual(laila.gpa, 4.0)
        self.assertEqual(len(reloaded.courses), 4)


if __name__ == "__main__":
    unittest.main()
