import re

from sqlalchemy import Column, ForeignKey, Integer, Unicode, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

engine = create_engine('sqlite:///files//courses.db')
Base = declarative_base()
Base.metadata.bind = engine
from sqlalchemy.orm import sessionmaker
db_session = sessionmaker()
db_session.bind = engine

primitives_type = {Integer, Unicode, String}


class Lecturer(Base):
    __tablename__ = 'lecturer'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Unicode, primary_key=True)
    name = Column(Unicode(250))
    hebrew_name = Column(Unicode(250))    
    email = Column(Unicode(250))
    office = Column(Unicode(250))
    phone = Column(Unicode(250))
    fax = Column(Unicode(250))
    title = Column(Unicode(250))
    honor = Column(Unicode(250))

    
    def __str__(self):
        return str(self.__dict__)
    
    def __repr__(self):
        return repr(self.__dict__)
    
class Course(Base):
    __tablename__ = 'course'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(250), nullable=False)
    hebrew_name = Column(Unicode(250), nullable=False)
    hebrew_departure =  Column(Unicode(250), nullable=False)
    departure =  Column(Unicode(250), nullable=False)
    semester = Column(Integer)
    start_time = Column(Integer)
    end_time = Column(Integer)
    day = Column(Integer)
    place =  Column(Unicode(250), nullable=False)
    kind =  Column(Unicode(250), nullable=False)
    building = Column(Unicode(250), nullable=False)
    lecturer_id = Column(Unicode, ForeignKey('lecturer.id'))
    lecturer = relationship(Lecturer)
    
    def __str__(self):
        return str(self.__dict__)
    
    def __repr__(self):
        return repr(self.__dict__)

#funny trick
Course.lecturer.type = Lecturer