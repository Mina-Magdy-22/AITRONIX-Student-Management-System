from exceptions import ValidationError

from .person import Person


class Teacher(Person):
    MIN_AGE = 21
    MAX_AGE = 75

    def __init__(self, teacher_id, name, age, email, department):
        super().__init__(teacher_id, name, age, email)
        self.department = department

    @property
    def department(self):
        return self._department

    @department.setter
    def department(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Department cannot be empty.")
        self._department = " ".join(value.split())

    def get_role(self):
        return "Teacher"

    def get_details(self):
        return (
            f"ID         : {self.person_id}\n"
            f"Name       : {self.name}\n"
            f"Role       : {self.get_role()}\n"
            f"Age        : {self.age}\n"
            f"Email      : {self.email}\n"
            f"Department : {self.department}"
        )

    def to_dict(self):
        data = super().to_dict()
        data["department"] = self.department
        return data

    @staticmethod
    def from_dict(data):
        return Teacher(data["id"], data["name"], data["age"], data["email"], data["department"])
