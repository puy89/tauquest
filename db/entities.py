from sqlalchemy import Column, ForeignKey, Integer, Unicode, String
from sqlalchemy.orm import relationship
from db import db_instance


class Lecturer(db_instance._base):
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

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Course(db_instance._base):
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
    start_time = Column(Integer)
    end_time = Column(Integer)
    day = Column(Integer)
    place = Column(Unicode(250), nullable=False)
    kind = Column(Unicode(250), nullable=False)
    building = Column(Unicode(250), nullable=False)
    lecturer_id = Column(Unicode, ForeignKey('lecturer.id'))
    lecturer = relationship(Lecturer)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


# funny trick
Course.lecturer.type = Lecturer
