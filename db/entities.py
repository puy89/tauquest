from sqlalchemy import Column, ForeignKey, Integer, Unicode, String, DateTime, Table, Enum
from sqlalchemy.orm import relationship
from db import db_instance


class CourseToLecturerMappingDB(db_instance._base):
    __tablename__ = "course_to_lecturer"
    course_id = Column(String, ForeignKey("course.id"), primary_key=True)
    lecturer_id = Column(String, ForeignKey("lecturer.id"), primary_key=True)
    course = relationship("db.entities.CourseDB", back_populates="lecturers")
    lecturer = relationship("db.entities.LecturerDB", back_populates="courses")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

class LecturerDB(db_instance._base):
    __tablename__ = 'lecturer'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Unicode, primary_key=True)
    name = Column(Unicode(250))
    site = Column(String(250), nullable=True)
    hebrew_name = Column(Unicode(250))
    email = Column(Unicode(250))
    office_building = Column(Unicode(250), nullable=True)
    office = Column(Unicode(250), nullable=True)
    phone = Column(Unicode(250))
    fax = Column(Unicode(250))
    title = Column(Unicode(250))
    honor = Column(Unicode(250))
    courses = relationship("db.entities.CourseToLecturerMappingDB", back_populates="lecturer")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class PythonDBClass(object):
    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


class CourseToLecturerMapping(PythonDBClass):
    __tablename__ = 'course_to_lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)

class Lecturer(PythonDBClass):
    __tablename__ = 'lecturer'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)


class CourseDB(db_instance._base):
    __tablename__ = 'course'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(String, primary_key=True)
    name = Column(Unicode(250), nullable=False)
    hebrew_name = Column(Unicode(250), nullable=False)
    hebrew_department = Column(Unicode(250), nullable=False)
    department = Column(Unicode(250), nullable=True)
    faculty = Column(Unicode(250), nullable=False)
    semester = Column(Integer)
    start_time = Column(Integer, nullable=True)
    end_time = Column(Integer, nullable=True)
    day = Column(Integer, nullable=True)
    moed_a = Column(DateTime, nullable=True)
    moed_b = Column(DateTime, nullable=True)
    place = Column(Unicode(250), nullable=False)
    kind = Column(Unicode(250), nullable=False)
    building = Column(Unicode(250), nullable=False)
    lecturers = relationship("db.entities.CourseToLecturerMappingDB", back_populates="course")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Course(PythonDBClass):
    __tablename__ = 'course'

    def __init__(self, c):
        self.__dict__ = dict(c.__dict__)
        # multiplicy?
        # self.lecturers = Lecturer(c.lecturer) if c.lecturer is not None else None

# # funny trick
# CourseDB.lecturers.type = LecturerDB
# LecturerDB.courses.type = CourseDB
