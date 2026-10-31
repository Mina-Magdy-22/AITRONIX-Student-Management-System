class SchoolError(Exception):
    pass


class ValidationError(SchoolError):
    pass


class NotFoundError(SchoolError):
    pass


class DuplicateError(SchoolError):
    pass


class EnrollmentError(SchoolError):
    pass
