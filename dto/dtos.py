

class DTOClass(object):
    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


class CourseToLecturerMapping(DTOClass):
    __tablename__ = 'course_to_lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

class LecturerDTO(DTOClass):
    __tablename__ = 'lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class CourseDTO(DTOClass):
    __tablename__ = 'course'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)
        # multiplicy?
        # self.lecturers = Lecturer(c.lecturer) if c.lecturer is not None else None
