import abc


class DTOClass(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        args = self.get_args()
        values_dict = self.__dict__
        return ', '.join("{0}: {1}".format(arg, values_dict[arg]) for arg in args)

    @abc.abstractmethod
    def get_args(self):
        return

class CourseToLecturerDTO(DTOClass):
    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class ExamDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.moed_a = c.moed_a
        self.moed_b = c.moed_b
        self.multi_course = c.multi_course_id

    def update_exam(self, multi_courses_map):
        self.multi_course = multi_courses_map.get(self.multi_course)

    def get_args(self):
        return [self.id, self.moed_a, self.moed_b]


    def get_args(self):
        return ["id", "moed_a", "moed_b"]

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

    def get_args(self):
        return ["id", "multi_course_id", "exam", "courses", "name", "department",
                "faculty", "semester"]


class OccurenceDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.start_time = c.start_time
        self.end_time = c.end_time
        self.full_start_time = c.day, c.start_time
        self.full_end_time = c.day, c.end_time
        self.day = c.day
        self.place = c.place
        self.building = c.building
        self.full_place = (c.building or '') + ' ' + (c.place or '')
        self.full_place = self.full_place.lstrip().rstrip() or None
        self.course = c.course_id

    def update_occurence(self, courses_map):
        self.course = courses_map.get(self.course)

    def get_args(self):
        return ["id", "start_time", "full_start_time", "full_end_time", "place", "building"]


class CourseDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.course_group_id = c.course_group_id
        self.kind = c.kind
        self.occurences = [OccurenceDTO(occurence) for occurence in c.occurences]
        self.lecturers = [LecturerDTO(lecturer.lecturer) for lecturer in c.lecturers]
        self.multi_course = c.multi_course_id

    def update_course(self, multi_courses_map):
        self.multi_course = multi_courses_map.get(self.multi_course)

    def get_args(self):
        return ["id", "course_group_id", "kind", "occurences", "lecturers"]


class PhoneDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.phone = c.phone
        self.lecturer = c.lecturer_id

    def update_phone(self, lecturers_map):
        self.lecturer = lecturers_map.get(int(self.lecturer))

    def get_args(self):
        return ["id", "phone"]


class LecturerDTO(DTOClass):
    def __init__(self, c):
        self.id = c.id
        self.name = c.name
        self.site = c.site
        self.hebrew_name = c.hebrew_name
        self.email = c.email
        self.office_building = c.office_building
        self.office = c.office
        self.full_office = (c.office_building or '') + ' ' + (c.office or '')
        self.full_office = self.full_office.lstrip().rstrip() or None
        self.phones = [PhoneDTO(phone) for phone in c.phones]
        self.fax = c.fax
        self.title = c.title
        self.honor = c.honor
        self.courses = [course.course.id for course in c.courses]

    def update_courses(self, course_id_to_course_map):
        self.courses = [course_id_to_course_map[id] for id in self.courses]

    def get_args(self):
        return ["id", "name", "site", "email", "office_building", "office", "phones", "fax", "title",
                "honor"]
