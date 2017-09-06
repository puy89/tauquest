import re
from datetime import datetime
from sqlalchemy import Integer, String, Unicode
from sqlalchemy.orm.attributes import InstrumentedAttribute
from db.entities import Course, Lecturer, CourseDB, LecturerDB



funcs = {'<': (lambda x, y: x is not None and y is not None and x < y, Integer),
         '>': (lambda x, y: x is not None and y is not None and x > y, Integer),
         '<=': (lambda x, y: x is not None and y is not None and x <= y, Integer),
         '>=': (lambda x, y: x is not None and y is not None and x >= y, Integer),
         'date_after': (lambda x, y: x is not None and y is not None and x < y, datetime),
         'date_before': (lambda x, y: x is not None and y is not None and x > y, datetime),
         'date_aftereq': (lambda x, y: x is not None and y is not None and x <= y, datetime),
         'date_beforeq': (lambda x, y: x is not None and y is not None and x >= y, datetime),
         'after': (lambda x, y: x is not None and y is not None and x.day == y.day and x.start_time >= y.end_time, Course),
         'before': (lambda x, y: x is not None and y is not None and x.day == y.day and y.start_time >= x.end_time, Course),#symmteric?
         'intersect': (lambda x, y: x is not None and y is not None and x.day == y.day and (y.start_time <= x.start_time < y.end_time or                                                                                   x.start_time <= y.start_time < x.end_time) , Course),
         'contains': (lambda x, y: x is not None and y is not None and y in x, String),
         'contained': (lambda x, y: x is not None and y is not None and x in y, String),
         'startswith': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         'initof': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         }

name_types = {Course: 'Course',
              Lecturer: 'Lecturer',
              Integer: 'Integer',
              String: 'String',
              Unicode: 'Unicode'}
types_name = {v: k for k, v in name_types.items()}

class DCS(object):
    pass

class Expression(DCS):
    pass


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
        return u'{}:{}'.format(name_types[self.type], self.id)
    
    def copy(self, span):
        return Entity(self.id, self.type, span)    

class Courses(Expression):
    def __init__(self, span=[]):
        self.type = Course
        self.is_func = False
        self.span = span

    def execute(self, db):
        return set(db.courses.values())

    def __str__(self):
        return 'Courses'
    
    def copy(self, span):
        return Courses(self, span)    



class Lecturers(Expression):
    def __init__(self, span=[]):
        self.type = Lecturer
        self.is_func = False
        self.span = span

    def execute(self, db):
        return set(db.lecturers.values())

    def __str__(self):
        return 'Lecturers'
    
    def copy(self, span):
        return Lecturers(self, span)    

class Intersect(Expression):
    def __init__(self, exp1, exp2, span=[]):
        self.exp1 = exp1
        self.exp2 = exp2
        self.type = exp1.type
        self.is_func = exp1.is_func and exp2.is_func
        self.span = span
        self.saved_res = None


        # assert exp1.type == exp2.type

    def execute(self, db):
        if self.saved_res:
            return self.saved_res
        exp1 = self.exp1
        exp2 = self.exp2
        if exp1.is_func:
            if exp2.is_func:
                return lambda x: exp1.execute(db)(x) and exp2.execute(db)(x)
            else:
                self.saved_res = {ent for ent in exp2.execute(db) if exp1.execute(db)(ent)}
                return self.saved_res
        elif exp2.is_func:
            self.saved_res = {ent for ent in exp1.execute(db) if exp2.execute(db)(ent)}
            return self.saved_res
        self.saved_res = exp1.execute(db) & exp2.execute(db)
        return self.saved_res

    def __str__(self):
        return '({}&{})'.format(self.exp1, self.exp2)
    
    def copy(self, span):
        return Intersect(self.exp1, self.exp2)    


class Predicate(DCS):
    def __init__(self, pred, span=()):
        if type(pred) is not str:
            self.unknown = True
            return
        self.pred = pred
        self.span = span
        self.is_attr = False
        self.is_db_join = False
        self.is_func = False
        self.is_rev = False
        self.is_lec = False
        self.unknown = False
        self.rtype = None
        self.ltype = None
        func_type = funcs.get(pred)
        if func_type is not None:
            self.ltype = self.rtype = func_type[1]
            self.func = func_type[0]
            self.is_func = True
            return
        if pred == 'teach':
            self.ltype = Course
            self.rtype = Lecturer
            self.is_db_join = True
            return
        if pred[:4] == 'rev_':
            self.pred = pred = pred[4:]
            self.is_rev = True
        attr = vars(CourseDB).get(pred)
        if attr is not None:
            if self.is_rev:
                self.rtype = type(attr.type)
                self.ltype = Course
            else:
                self.rtype = Course
                self.ltype = type(attr.type)
                if pred == 'lecturer':
                    assert not self.is_rev
                    self.ltype = Lecturer
                    self.rtype = Course

            self.is_attr = True
        else:
            if pred[:4] == 'lec_':
                self.pred = pred = pred[4:]
                self.is_lec = True
            attr = vars(LecturerDB).get(pred)
            if attr is not None:
                if self.is_rev:
                    self.rtype = type(attr.type)
                    self.ltype = Lecturer
                else:
                    self.rtype = Lecturer
                    self.ltype = type(attr.type)
                self.is_attr = True
            else:
                self.unknown = True

    def __str__(self):
        return '{}{}{}'.format('rev_' * self.is_rev, 'lec_' * self.is_lec, self.pred)
    
    def copy(self, span):
        return Predicate(str(self), span)


class Join(Expression):
    def __init__(self, pred, un, span=(), pred_span=()):
        self.un = un
        self.span = span
        if isinstance(pred, str):
            self.pred = Predicate(pred, pred_span)
        else:
            self.pred = pred
        self.is_attr = self.pred.is_attr

        self.is_attr = self.pred.is_attr
        self.is_db_join = self.pred.is_db_join
        self.is_func = self.pred.is_func
        self.is_rev = self.pred.is_rev
        if self.pred.is_func:
            self.type = self.un.type
        else:
            self.type = self.pred.ltype
        self.saved_res = None

    def execute(self, db):#what a fucked function!!!!
        if self.saved_res:
            return self.saved_res
        un = self.un
        pred = self.pred.pred
        if self.is_func:
            if self.type == Course:
                func = self.pred.func
                ents = un.execute(db)
                if not ents:
                    return{}
                self.saved_res = {c for c in db.courses.values()
                        if any(func(c, ent) for ent in ents)}
                return self.saved_res
            elif self.type == Lecturer:
                func = self.pred.func
                ents = un.execute(db)
                if not ents:
                    return {}
                self.saved_res =  {c for c in db.lecturers.values()
                        if any(func(c, ent) for ent in ents)}
                return self.saved_res
            else:
                if self.un.is_func:
                    pass#estoric!
                else:
                    func = self.pred.func
                    ents = un.execute(db)
                    return lambda x: any(func(x, ent) for ent in ents)
        elif self.is_rev:
            ents = un.execute(db)
            if un.is_func and un.type != Course and un.type != Lecturer:
                if self.type == Course:
                    self.saved_res = {ent for ent in db.courses.values() if ents(getattr(ent, pred))}
                    return self.saved_res
                if self.type == Lecturer:
                    self.saved_res = {ent for ent in db.lecturers.values() if ents(getattr(ent, pred))}
                    return self.saved_res
            else:
                if self.type == Course:
                    self.saved_res = {ent for ent in db.courses.values() if getattr(ent, pred) in ents}
                    return self.saved_res
                if self.type == Lecturer:
                    self.saved_res = {ent for ent in db.lecturers.values() if getattr(ent, pred) in ents}
                    return self.saved_res
        elif self.is_attr:
            self.saved_res = {getattr(ent, pred) if ent is not None else None for ent in un.execute(db)}
            return self.saved_res
        elif self.is_db_join:
            # TODO: other joins?
            self.saved_res = {c for ent in un.execute(db) for c in db.courses.values() if c.lecturer_id == ent.id}
            return self.saved_res

    def __str__(self):
        return u'({}.{})'.format(self.pred, self.un)
    
    def copy(self, span):
        return Join(self.pred, self.un, span)    

class LexEnt(Expression):
    def __init__(self, words, type, span=()):
        self.words = words
        self.span = span
        self.type = type
        self.is_func = False
        self.saved_res = None
    
    def execute(self, db):
        if self.saved_res:
            return self.saved_res
        if self.type == Course:
            d = db.courses_words_dict
        elif self.type == Lecturer:
            d = db.lecturers_words_dict
        else:
            assert False, 'LexEnt is only Lecturer or Course'
        for word in self.words:
            v = d.get(word)
            if v is None:
                self.saved_res = set()
                return self.saved_res
            s, d = v
            if not d:
                self.saved_res = s
                return self.saved_res
        #d can be set or dict
        self.saved_res = s
        return self.saved_res
    
    def __str__(self):
        return 'lex_ent_{}({})'.format(self.type.__tablename__, ','.join(self.words))

class Aggregation(DCS):
    def __init__(self, exp=None, span=[]):
        self.exp = exp
        self.span = span
        self.is_func = False
        
    def copy(self, span):
        return type(self)(self.exp, span)


class Count(Aggregation):
    # TODO: handle mutiplicity

    def execute(self, db):
        return {len(self.exp.execute(db))}

    def __str__(self):
        return 'count({})'.format(self.exp)


class Max(Aggregation):
    def execute(self, db):
        return {max(self.exp.execute(db))}

    def __str__(self):
        return 'max{}'.format(self.exp)


class Min(Aggregation):
    def execute(self, db):
        return {min(self.exp.execute(db))}

    def __str__(self):
        return 'min({})'.format(self.exp)


aggregats = dict(min=Min,
                 count=Count,
                 max=Max)
aggregat_p = re.compile('({})\\(.+\\)'.format('|'.join(aggregats)))


# TO DO: argmin argmax?

def parse_dcs(exp):
    in_parents = exp[0] == '(' and exp[-1] == ')'
    match = aggregat_p.match(exp)
    if match:
        assert match.start() == 0 and match.end() == len(exp)  # only aggregation in the top
        aggregat, = match.groups()
        aggregat_cls = aggregats[aggregat]
        # TO DO? handle aggregation combine with not aggregation
        return aggregat_cls(parse_dcs(exp[len(aggregat) + 1: -1]))

    counter = 0
    for i, c in enumerate(exp):
        if c == '(':
            counter += 1
        elif c == ')':
            counter -= 1
        elif counter == 0:
            if c == '&':
                return Intersect(parse_dcs(exp[:i]), parse_dcs(exp[i + 1:]))
            if c == '.':
                return Join(parse_dcs(exp[:i]), parse_dcs(exp[i + 1:]))
            if c == ':':
                if exp[:i] == 'Unicode':
                    return Entity(unicode(exp[i + 1:]), Unicode)
                if exp[:i] == 'Integer':
                    return Entity(int(exp[i + 1:]), Integer)
                elif exp[:i] == 'Course':
                    return Entity(int(exp[i + 1:]), Course)
                return Entity(exp[i + 1:], types_name[exp[:i]])
            in_parents = False
        assert counter >= 0
    if in_parents:
        return parse_dcs(exp[1:-1])
    if exp == 'Courses':
        return Courses()
    if exp == 'Lectures':
        return Lecturers()
    return exp

type2preds = {}
for func in funcs:
    pred = Predicate(func)
    type2preds.setdefault(pred.rtype, []).append(pred)
for k, v in vars(CourseDB).iteritems():
    if type(v) is InstrumentedAttribute:
        pred = Predicate(k)
        type2preds.setdefault(pred.rtype, []).append(pred)
        if k != 'lecturer':
            pred = Predicate('rev_'+k)
            type2preds.setdefault(pred.rtype, []).append(pred)
    
for k, v in vars(LecturerDB).iteritems():
    if type(v) is InstrumentedAttribute:
        k = 'lec_' + k
        pred = Predicate(k)
        type2preds.setdefault(pred.rtype, []).append(pred)
        pred = Predicate('rev_'+k)
        type2preds.setdefault(pred.rtype, []).append(pred)
