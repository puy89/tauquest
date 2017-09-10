from sqlalchemy import Column, ForeignKey, Integer, Unicode, String, DateTime, Table, Enum
from sqlalchemy.orm import relationship, backref
from db import db_instance


class CourseToLecturer(db_instance._base):
    __tablename__ = "course_to_lecturer"
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)
    lecturer_id = Column(Integer, ForeignKey("lecturer.id"), primary_key=True)
    course = relationship("Course", back_populates="lecturers")
    lecturer = relationship("Lecturer", back_populates="courses")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Exam(db_instance._base):
    __tablename__ = "exam"
    id = Column(Integer, primary_key=True, autoincrement=True)
    moed_a = Column(DateTime, nullable=True)
    moed_b = Column(DateTime, nullable=True)
    multi_course_id = Column(Integer, ForeignKey("multi_course.id"))


class MultiCourse(db_instance._base):
    __tablename__ = "multi_course"
    id = Column(Integer, primary_key=True, autoincrement=True)
    multi_course_id = Column(String)
    exam = relationship(Exam, uselist=False, lazy='joined')
    courses = relationship("Course", lazy='joined')
    name = Column(Unicode(250), nullable=False)
    hebrew_name = Column(Unicode(250), nullable=False)
    hebrew_department = Column(Unicode(250), nullable=False)
    department = Column(Unicode(250), nullable=True)
    faculty = Column(Unicode(250), nullable=False)
    semester = Column(Integer)



class Occurence(db_instance._base):
    __tablename__ = "occurence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Integer, nullable=True)
    end_time = Column(Integer, nullable=True)
    day = Column(Integer, nullable=True)
    place = Column(Unicode(250), nullable=False)
    building = Column(Unicode(250), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"))


class Course(db_instance._base):
    __tablename__ = 'course'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True, autoincrement=True)
    multi_course_id = Column(Integer, ForeignKey("multi_course.id"))
    course_group_id = Column(String)
    kind = Column(Unicode(250), nullable=False)
    occurences = relationship(Occurence, lazy='joined')
    lecturers = relationship(CourseToLecturer, back_populates="course", lazy='joined')

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Phone(db_instance._base):
    __tablename__ = "phone"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(Unicode(250), nullable=False)
    lecturer_id = Column(String, ForeignKey("lecturer.id"))


class Lecturer(db_instance._base):
    __tablename__ = 'lecturer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(250))
    site = Column(String(250), nullable=True)
    hebrew_name = Column(Unicode(250))
    email = Column(Unicode(250))
    office_building = Column(Unicode(250), nullable=True)
    office = Column(Unicode(250), nullable=True)
    phones = relationship(Phone, lazy='joined')
    fax = Column(Unicode(250))
    title = Column(Unicode(250))
    honor = Column(Unicode(250))
    courses = relationship(CourseToLecturer, back_populates="lecturer", lazy='joined')

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

Course.lecturers.type = list
Course.occurences.type = list
Lecturer.phones.type = list
Lecturer.courses.type = list
