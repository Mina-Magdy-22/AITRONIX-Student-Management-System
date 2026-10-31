from exceptions import ValidationError


class Course:
    def __init__(self, code, name, capacity=30, teacher_id=None):
        if not isinstance(code, str) or not code.strip() or " " in code.strip():
            raise ValidationError("Course code cannot be empty or contain spaces.")
        self._code = code.strip().upper()
        self.name = name
        self.capacity = capacity
        self.teacher_id = teacher_id

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Course name cannot be empty.")
        self._name = " ".join(value.split())

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, value):
        valid = isinstance(value, int) and not isinstance(value, bool)
        if not valid or not 1 <= value <= 200:
            raise ValidationError("Capacity must be a whole number between 1 and 200.")
        self._capacity = value

    def to_dict(self):
        return {"code": self.code, "name": self.name, "capacity": self.capacity, "teacher_id": self.teacher_id}

    @staticmethod
    def from_dict(data):
        return Course(data["code"], data["name"], data["capacity"], data.get("teacher_id"))

    def __str__(self):
        return f"{self.code} - {self.name}"
