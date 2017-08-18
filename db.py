import sqlalchemy


import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, Unicode, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import re
engine = create_engine('sqlite:///courses.db')
Base = declarative_base()
Base.metadata.bind = engine
from sqlalchemy.orm import sessionmaker
DBSession = sessionmaker()
DBSession.bind = engine
from sqlalchemy.orm.attributes import InstrumentedAttribute as Attr

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
    

funcs = {'<': lambda x, y: x < y,
         '>': lambda x, y: x > y,
         '<=': lambda x, y: x <= y,
         '>=': lambda x, y: x >= y,
         'contains': lambda x, y: y in x,
         'contained': lambda x, y: x in y,
         'startswith': lambda x, y: x.startswith(y),
         'initof': lambda x, y: x.startswith(y),
        }

name_types = {Course: 'Course',
              Lecturer: 'Lecturer',
              Integer: 'Integer',
              String: 'String',
              Unicode: 'Unicode'}
types_name = {v: k for k, v in name_types.items()}

class Expression(object):
    pass

class Courses(Expression):
    def __init__(self, span=[]):
        self.type = Course
        self.is_func = False
        self.span = span

        
    def execute(self, db):
        return set(db.courses.values())
    
    def __str__(self):
        return 'Courses'

class Lecturers(Expression):
    def __init__(self, span=[]):
        self.type = Lecturer
        self.is_func = False
        self.span = span

        
    def execute(self, db):
        return set(db.lecturers.values())

    def __str__(self):
        return 'Lecturers'

    
class Entity(Expression):
    def __init__(self, id, type, span=[]):
        self.id = id
        self.type = type
        self.is_func = False
        self.span = span
        
    def execute(self, db):
        type = self.type
        if type is Course:
            return {db.courses[self.id]}
        elif type is Lecturer:
            return {db.lecturers[self.id]}
        else:
            return {self.id}

    def __str__(self):
        return '{}:{}'.format(name_types[self.type], self.id)
    
            

class Intersect(Expression):
    def __init__(self, exp1, exp2, span=[]):
        self.exp1 = exp1
        self.exp2 = exp2
        self.type = exp1.type
        self.is_func = exp1.is_func and exp2.is_func
        self.span = span

        
        #assert exp1.type == exp2.type
    
    def execute(self, db):
        exp1 = self.exp1
        exp2 = self.exp2
        if exp1.is_func:
            if exp2.is_func:
                return lambda x: exp1.execute(db)(x) and exp2.execute(db)(x)
            else:
                return {ent for ent in exp2.execute(db) if exp1.execute(db)(ent)}
        elif exp2.is_func:    
            return {ent for ent in exp1.execute(db) if exp2.execute(db)(ent)}        
        return exp1.execute(db) & exp2.execute(db)
    
    def __str__(self):
        return '({}&{})'.format(self.exp1, self.exp2)


    
class Join(Expression):
    def __init__(self, pred, un, span=[], pred_span=[]):
        self.pred = pred
        self.un = un
        self.is_attr = False
        self.is_db_join = False
        self.is_func = False
        self.is_rev = False
        self.span = span
        self.pred_span = span
        if pred == 'teach' and un.type == Lecturer:
            self.type = Course
            self.is_db_join = True
        if pred[:4] == 'rev_':
            self.pred = pred = pred[4:]
            self.is_rev = True
        attr = vars(Course).get(pred)
        if attr is not None:
            if self.is_rev:
                self.type = Course
            else:
                self.type = type(attr.type)
            self.is_attr = True
        else:
            attr = vars(Lecturer).get(pred)
            if attr is not None:
                if self.is_rev:
                    self.type = Lecturer
                else:
                    self.type = type(attr.type)
                self.is_attr = True
            else:
                self.is_func = True
                self.type = un.type
            
    
    def execute(self, db):
        un = self.un
        pred = self.pred
        if self.is_func:
            if self.un.is_func:
                pass
                #TODO bom
            else:
                func = funcs[pred]
                ents = un.execute(db)
                return lambda x: any(func(x, ent) for ent in ents)
        elif self.is_rev:
            ents = un.execute(db)
            if un.is_func:
                if self.type == Course:
                    return {ent for ent in db.courses.values() if ents(vars(ent)[pred])}
                if self.type == Lecturer:
                    return {ent for ent in db.lecturers.values() if ents(vars(ent)[pred])}
            else:    
                if self.type == Course:
                    return {ent for ent in db.courses.values() if vars(ent)[pred] in ents}
                if self.type == Lecturer:
                    return {ent for ent in db.lecturers.values() if vars(ent)[pred] in ents}
        elif self.is_attr:
            return {getattr(ent, pred) for ent in un.execute(db)}
        elif self.is_db_join:
            #TODO: other joins?
            return {ent for ent in un.execute(db) for c in db.courses if c.course.lecturer_id == ent.id}

    def __str__(self):
        return '({}{}.{})'.format('rev_'*self.is_rev, self.pred, self.un)

class Count(Expression):
    #TODO: handle mutiplicity
    def __init__(self, exp, span=[]):
        self.exp = exp
        self.span = span
    
    def execute(self, db):
        return len(self.exp.execute(db))

class Max(Expression):
    def __init__(self, exp, span=[]):
        self.exp = exp
        self.span = span
    
    def execute(self, db):
        return max(self.exp.execute(db))

class Min(Expression):
    def __init__(self, exp, span=[]):
        self.exp = exp
        self.span = span
    
    def execute(self, db):
        return min(self.exp.execute(db))

    
#TO DO: max min argmax?
    
def parse_dcs(exp):
    in_parents = exp[0] == '(' and exp[-1] == ')'
    #TO DO: with regexp
    if exp.startswith('count'):
        #TO DO? handle aggregation combine with not aggregation
        return Count(parse_dcs(exp[len('count') +  1: -1]))
    elif exp.startswith('min'):
        #TO DO? handle aggregation combine with not aggregation
        return Min(parse_dcs(exp[len('min') +  1: -1]))
    elif exp.startswith('max'):
        #TO DO? handle aggregation combine with not aggregation
        return Max(parse_dcs(exp[len('max') +  1: -1]))
    
    counter = 0
    for i, c in enumerate(exp):
        if c == '(':
            counter += 1
        elif c == ')':
            counter -= 1
        elif counter == 0: 
            if c == '&':
                return Intersect(parse_dcs(exp[:i]), parse_dcs(exp[i+1:]))
            if c == '.':
                return Join(parse_dcs(exp[:i]), parse_dcs(exp[i+1:]))
            if c == ':':
                if exp[:i] == 'Unicode':
                    return Entity(unicode(exp[i+1:]), Unicode)
                if exp[:i] == 'Integer':
                    return Entity(int(exp[i+1:]), Integer)
                elif exp[:i] == 'Course':
                    return Entity(int(exp[i+1:]), Course)
                return Entity(exp[i+1:], types_name[exp[:i]])
            in_parents = False
        assert counter >= 0
    if in_parents:
        return parse_dcs(exp[1:-1])        
    if exp == 'Courses':
        return Courses()
    if exp == 'Lectures':
        return Lectures()
    return exp

    
class DB(object):
    def __init__(self):
        self.s = DBSession()
        self.courses = {c.id: c for c in self.s.query(Course)}
        self.lecturers = {l.id: l for l in self.s.query(Lecturer)}
    
     