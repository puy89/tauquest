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
    def __init__(self, c):
        self.moed_a = c.moed_a
        self.moed_b = c.moed_b


class MultiCourseDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.multi_course_id = c.multi_course_id
        self.exam = ExamDTO(c.exam)
        self.courses = [CourseDTO(course) for course in c.courses]
        self.name = c.name
        self.hebrew_name = c.hebrew_name
        self.hebrew_department = c.hebrew_department
        self.department = c.department
        self.faculty = c.faculty
        self.semester = c.semester


class OccurenceDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.start_time = c.start_time
        self.end_time = c.end_time
        self.day = c.day
        self.place = c.place
        self.building = c.building


class CourseDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.multi_course_id = c.multi_course_id
        self.course_group_id = c.course_group_id
        self.kind = c.kind
        self.occurences = [OccurenceDTO(occurence) for occurence in c.occurences]
        self.lecturers = [LecturerDTO(lecturer.lecturer) for lecturer in c.lecturers]


class PhoneDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.phone = c.phone


class LecturerDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.name = c.name
        self.site = c.site
        self.hebrew_name = c.hebrew_name
        self.email = c.email
        self.office_building = c.office_building
        self.office = c.office
        self.phones = [PhoneDTO(phone) for phone in c.phones]
        self.fax = c.fax
        self.title = c.title
        self.honor = c.honor
        self.courses = [course.course.id for course in c.courses]

    def update_courses(self, course_id_to_course_map):
        self.courses = [course_id_to_course_map[id] for id in self.courses]