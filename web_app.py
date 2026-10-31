import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from exceptions import SchoolError
from models import letter_grade
from school import School

PAGE = Path(__file__).parent / "static" / "index.html"
school = None


def student_json(student):
    data = student.to_dict()
    data.update(
        role=student.get_role(),
        gpa=student.gpa,
        has_grades=student.has_grades,
        standing=student.standing(),
        max_courses=student.max_courses(),
        enrollments=[
            {
                "code": code,
                "name": school.courses[code].name,
                "grade": grade,
                "letter": "-" if grade is None else letter_grade(grade),
            }
            for code, grade in student.grades.items()
        ],
    )
    return data


def course_json(course):
    data = course.to_dict()
    data["students"] = [{"id": s.person_id, "name": s.name} for s in school.roster(course.code)]
    return data


def get_data():
    return {
        "students": [student_json(s) for s in school.students.values()],
        "teachers": [t.to_dict() for t in school.teachers.values()],
        "courses": [course_json(c) for c in school.courses.values()],
    }


ACTIONS = {
    "add_student": lambda d: school.add_student(
        d.get("name"), d.get("age"), d.get("email"), d.get("major"), d.get("type") or "undergraduate", d.get("thesis")),
    "update_student": lambda d: school.update_student(
        d.get("id"), d.get("name"), d.get("age"), d.get("email"), d.get("major")),
    "delete_student": lambda d: school.delete_student(d.get("id")),
    "add_teacher": lambda d: school.add_teacher(d.get("name"), d.get("age"), d.get("email"), d.get("department")),
    "delete_teacher": lambda d: school.delete_teacher(d.get("id")),
    "add_course": lambda d: school.add_course(d.get("code"), d.get("name"), d.get("capacity")),
    "delete_course": lambda d: school.delete_course(d.get("code")),
    "assign_teacher": lambda d: school.assign_teacher(d.get("teacher_id"), d.get("course_code")),
    "enroll": lambda d: school.enroll(d.get("student_id"), d.get("course_code")),
    "drop": lambda d: school.drop(d.get("student_id"), d.get("course_code")),
    "grade": lambda d: school.set_grade(d.get("student_id"), d.get("course_code"), d.get("grade")),
    "demo": lambda d: school.add_sample_data(),
}


class Handler(BaseHTTPRequestHandler):
    def send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        self.send_body(status, json.dumps(payload).encode("utf-8"), "application/json")

    def do_GET(self):
        if self.path == "/":
            self.send_body(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/data":
            self.send_json(200, get_data())
        else:
            self.send_json(404, {"error": "Not found."})

    def do_POST(self):
        action = ACTIONS.get(self.path[len("/api/"):]) if self.path.startswith("/api/") else None
        if action is None:
            self.send_json(404, {"error": "Not found."})
        elif "application/json" not in self.headers.get("Content-Type", ""):
            self.send_json(415, {"error": "Content-Type must be application/json."})
        else:
            try:
                length = int(self.headers.get("Content-Length") or 0)
                data = json.loads(self.rfile.read(length) or b"{}")
                action(data)
                self.send_json(200, {"ok": True})
            except (SchoolError, ValueError) as error:
                self.send_json(400, {"error": str(error)})
            except Exception:
                self.send_json(500, {"error": "Something went wrong on the server."})

    def log_message(self, format, *args):
        pass


def main():
    global school
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--demo", action="store_true", help="load sample data if the data is empty")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    try:
        school = School()
    except SchoolError as error:
        print("Fatal error:", error)
        return
    if args.demo:
        print("Sample data loaded." if school.add_sample_data() else "Data already exists.")

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Running at {url} (press Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
