

class DTOClass(object):
    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


class CourseToLecturerDTO(DTOClass):
    __tablename__ = 'course_to_lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class ExamDTO(DTOClass):
    __tablename__ = 'exam'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class MultiCourseDTO(DTOClass):
    __tablename__ = 'multi_course'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class OccurenceDTO(DTOClass):
    __tablename__ = 'occurence'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class CourseDTO(DTOClass):
    __tablename__ = 'course'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class PhoneDTO(DTOClass):
    __tablename__ = 'phone'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)



class LecturerDTO(DTOClass):
    __tablename__ = 'lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

