import re
from datetime import datetime
from numpy import inf
from sqlalchemy import Integer, String, Unicode
from sqlalchemy.orm.attributes import InstrumentedAttribute
from db.entities import Course, Lecturer
from dto.dtos import CourseDTO, LecturerDTO

future_time = datetime.now().replace(year=9999)
past_time =  datetime.now().replace(year=1980)

funcs = {'<': (lambda x, y: x is not None and y is not None and x < y, Integer),
         '>': (lambda x, y: x is not None and y is not None and x > y, Integer),
         '<=': (lambda x, y: x is not None and y is not None and x <= y, Integer),
         '>=': (lambda x, y: x is not None and y is not None and x >= y, Integer),
         'date_after': (lambda x, y: x is not None and y is not None and x < y, datetime),
         'date_before': (lambda x, y: x is not None and y is not None and x > y, datetime),
         'date_aftereq': (lambda x, y: x is not None and y is not None and x <= y, datetime),
         'date_beforeq': (lambda x, y: x is not None and y is not None and x >= y, datetime),
         'after': (lambda x, y: x is not None and y is not None and x.day == y.day and x.start_time >= y.end_time, CourseDTO),
         'before': (lambda x, y: x is not None and y is not None and x.day == y.day and y.start_time >= x.end_time, CourseDTO),#symmteric?
         'intersect': (lambda x, y: x is not None and y is not None and x.day == y.day and (y.start_time <= x.start_time < y.end_time or                                                                                   x.start_time <= y.start_time < x.end_time) , CourseDTO),
         'contains': (lambda x, y: x is not None and y is not None and y in x, String),
         'contained': (lambda x, y: x is not None and y is not None and x in y, String),
         'startswith': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         'initof': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         }

name_types = {CourseDTO: 'Course',
              LecturerDTO: 'Lecturer',
              Integer: 'Integer',
              String: 'String',
              Unicode: 'Unicode'}
types_name = {v: k for k, v in name_types.items()}

pred2type = dict(start_time='hour',
                 end_time='hour',
                 department='department',
                 faculty='faculty',
                 semsester='semsester',
                 kind='kind',
                 day='day',
                 building='building',
                 office_building='building',
                 place='room',
                 office='room',
                 phone='phone',
                 fax='phone',
                 title='title',
                 honor='honor',
                 
                )

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
        if type is CourseDTO:
            return {db.courses[self.id]}
        elif type is LecturerDTO:
            return {db.lecturers[self.id]}
        else:
            return {self.id}

    def __str__(self):
        return u'{}:{}'.format(name_types[self.type], self.id)
    
    def copy(self, span):
        return Entity(self.id, self.type, span)    

class Courses(Expression):
    def __init__(self, span=[]):
        self.type = CourseDTO
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
        self.type = LecturerDTO
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

class BasePredicate(DCS):
    pass

class Predicate(BasePredicate):
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
            self.ltype = CourseDTO
            self.rtype = LecturerDTO
            self.is_db_join = True
            return
        if pred[:4] == 'rev_':
            self.pred = pred = pred[4:]
            self.is_rev = True
        attr = vars(Course).get(pred)
        if attr is not None:
            if self.is_rev:
                self.rtype = type(attr.type)
                self.ltype = CourseDTO
            else:
                self.rtype = CourseDTO
                self.ltype = type(attr.type)
                if pred == 'lecturer':
                    assert not self.is_rev
                    self.ltype = LecturerDTO
                    self.rtype = CourseDTO

            self.is_attr = True
        else:
            if pred[:4] == 'lec_':
                self.pred = pred = pred[4:]
                self.is_lec = True
            attr = vars(Lecturer).get(pred)
            if attr is not None:
                if self.is_rev:
                    self.rtype = type(attr.type)
                    self.ltype = LecturerDTO
                else:
                    self.rtype = LecturerDTO
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
            if self.type == CourseDTO:
                func = self.pred.func
                ents = un.execute(db)
                if not ents:
                    return{}
                self.saved_res = {c for c in db.courses.values()
                        if any(func(c, ent) for ent in ents)}
                return self.saved_res
            elif self.type == LecturerDTO:
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
            if un.is_func and un.type != CourseDTO and un.type != LecturerDTO:
                if self.type == CourseDTO:
                    self.saved_res = {ent for ent in db.courses.values() if ents(getattr(ent, pred))}
                    return self.saved_res
                if self.type == LecturerDTO:
                    self.saved_res = {ent for ent in db.lecturers.values() if ents(getattr(ent, pred))}
                    return self.saved_res
            else:
                if self.type == CourseDTO:
                    self.saved_res = {ent for ent in db.courses.values() if getattr(ent, pred) in ents}
                    return self.saved_res
                if self.type == LecturerDTO:
                    self.saved_res = {ent for ent in db.lecturers.values() if getattr(ent, pred) in ents}
                    return self.saved_res
        elif self.is_attr:
            self.saved_res = {getattr(ent, pred) if ent is not None else None for ent in un.execute(db)}
            return self.saved_res
        elif self.is_db_join:
            # TODO: other joins?
            ents = un.execute(db)
            self.saved_res = {c for c in db.courses.values() if c.lecturer in ents}
            return self.saved_res

    def __str__(self):
        return u'({}.{})'.format(self.pred, self.un)
    
    def copy(self, span):
        return Join(self.pred.copy(span), self.un.copy(span), span)    

class LexEnt(Expression):
    def __init__(self, words, ent_type, span=()):
        self.words = words
        self.span = span
        self.ent_type = ent_type
        if ent_type == Course or ent_type == Lecturer:
            self.type = ent_type
        else:
            self.type = Unicode
        self.is_func = False
        self.saved_res = None
    
    def execute(self, db):
        if self.saved_res:
            return self.saved_res
        d = db.type2words_dict[self.ent_type]
        for word in self.words:
            if not d:
                self.saved_res = set()
                return self.saved_res
            v = d.get(word)
            if v is None:
                self.saved_res = set()
                return self.saved_res
            s, d = v
        #d can be set or dict
        self.saved_res = s
        return self.saved_res
    
    def __str__(self):
        return 'lex_ent_{}({})'.format(self.ent_type if self.type == Unicode else self.ent_type.__tablename__, ','.join(self.words))

class Aggregation(DCS):
    def __init__(self, exp=None, span=[], type=None):
        self.exp = exp
        self.span = span
        self.is_func = False
        self.rtype = type
        
    def copy(self, span, exp=None):
        return type(self)(exp or self.exp, span)


class Count(Aggregation):
    # TODO: handle mutiplicity
    def __init__(self, exp=None, span=[]):
        Aggregation.__init__(self, exp, span, None)
        
        

    def execute(self, db):
        return {len(self.exp.execute(db))}

    def __str__(self):
        return 'count({})'.format(self.exp)


class Max(Aggregation):
    def __init__(self, exp=None, span=[]):
        Aggregation.__init__(self, exp, span, None)

    def execute(self, db):
        return {max(self.exp.execute(db))}

    def __str__(self):
        return 'max{}'.format(self.exp)


class Min(Aggregation):
    def __init__(self, exp=None, span=[]):
        Aggregation.__init__(self, exp, span, None)

    def execute(self, db):
        return {min(self.exp.execute(db))}

    def __str__(self):
        return 'min{}'.format(self.exp)
    
    
class Arg(Aggregation):
    def __init__(self, exp=None, span=[], rtype=None, attr=None, ext_obj=None, func=None):
        Aggregation.__init__(self, exp, span, rtype)
        self.attr = attr
        self.ext_obj = ext_obj
        self.func = func
    
    
    def execute(self, db):
        return {self.func(self.exp.execute(db), key=lambda c: getattr(c, self.attr) or self.ext_obj)}

    def __str__(self):
        return 'arg{}_{}{}'.format(func.__name__, self.exp)


class Earliest(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'start_time', inf, min)
    
    def __str__(self):
        return 'earliest{}'.format(self.exp)


class Latest(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'start_time', -inf, max)

    def __str__(self):
        return 'latest{}'.format(self.exp)

class EarliestMoedA(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'moed_a', future_time, min)
    
    def __str__(self):
        return 'earliest_moeda{}'.format(self.exp)


class LatestMoedA(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'moed_a', past_time, max)

    def __str__(self):
        return 'latest_moeda{}'.format(self.exp)

class EarliestMoedB(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'moed_b', future_time, min)
    
    def __str__(self):
        return 'earliest_moedb{}'.format(self.exp)


class LatestMoedB(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, CourseDTO, 'moed_b', past_time, max)

    def __str__(self):
        return 'latest_moedb{}'.format(self.exp)

    
    
aggregats = dict(min=Min,
                 count=Count,
                 max=Max,
                 earliest=Earliest,
                 latest=Latest,
                 earliestmoeda=EarliestMoedA,
                 latestmoeda=LatestMoedA,
                 earliestmoedb=EarliestMoedB,
                 latestmoedb=LatestMoedB)
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
                    return Entity(int(exp[i + 1:]), CourseDTO)
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
for k, v in vars(Course).iteritems():
    if type(v) is InstrumentedAttribute:
        pred = Predicate(k)
        type2preds.setdefault(pred.rtype, []).append(pred)
        if k != 'lecturer':
            pred = Predicate('rev_'+k)
            type2preds.setdefault(pred.rtype, []).append(pred)
    
for k, v in vars(Lecturer).iteritems():
    if type(v) is InstrumentedAttribute:
        k = 'lec_' + k
        pred = Predicate(k)
        type2preds.setdefault(pred.rtype, []).append(pred)
        pred = Predicate('rev_'+k)
        type2preds.setdefault(pred.rtype, []).append(pred)
