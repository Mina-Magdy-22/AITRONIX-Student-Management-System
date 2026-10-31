from abc import ABC, abstractmethod

from exceptions import ValidationError


class Person(ABC):
    MIN_AGE = 1
    MAX_AGE = 120

    def __init__(self, person_id, name, age, email):
        self._person_id = person_id
        self.name = name
        self.age = age
        self.email = email

    @property
    def person_id(self):
        return self._person_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Name cannot be empty.")
        if any(char.isdigit() for char in value):
            raise ValidationError("Name cannot contain digits.")
        self._name = " ".join(value.split())

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        valid = isinstance(value, int) and not isinstance(value, bool)
        if not valid or not self.MIN_AGE <= value <= self.MAX_AGE:
            raise ValidationError(f"Age must be a whole number between {self.MIN_AGE} and {self.MAX_AGE}.")
        self._age = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        email = value.strip().lower() if isinstance(value, str) else ""
        name_part, _, domain = email.partition("@")
        if not name_part or "." not in domain or " " in email:
            raise ValidationError("Invalid email address.")
        self._email = email

    @abstractmethod
    def get_role(self):
        pass

    @abstractmethod
    def get_details(self):
        pass

    def to_dict(self):
        return {"id": self.person_id, "name": self.name, "age": self.age, "email": self.email}

    def __str__(self):
        return f"[{self.person_id}] {self.name} ({self.get_role()})"
