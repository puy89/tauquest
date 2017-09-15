import re
from datetime import datetime
from numpy import inf, mean
from sqlalchemy import Integer, String, Unicode
from sqlalchemy.orm.attributes import InstrumentedAttribute
from db.entities import Course, Lecturer, MultiCourse, Occurence, Phone, Exam
from dto.dtos import CourseDTO, LecturerDTO, MultiCourseDTO, OccurenceDTO, ExamDTO, PhoneDTO

future_time = datetime.now().replace(year=9999)
past_time =  datetime.now().replace(year=1980)

funcs = {'<': (lambda x, y: x is not None and y is not None and x < y, 'time'),
         '>': (lambda x, y: x is not None and y is not None and x > y, 'time'),
         '<=': (lambda x, y: x is not None and y is not None and x <= y, 'time'),
         '>=': (lambda x, y: x is not None and y is not None and x >= y, 'time'),
         'hour<': (lambda x, y: x is not None and y is not None and x < y, 'hour'),
         'hour>': (lambda x, y: x is not None and y is not None and x > y, 'hour'),
         'hour<=': (lambda x, y: x is not None and y is not None and x <= y, 'hour'),
         'hour>=': (lambda x, y: x is not None and y is not None and x >= y, 'hour'),
         'date_after': (lambda x, y: x is not None and y is not None and x < y, datetime),
         'date_before': (lambda x, y: x is not None and y is not None and x > y, datetime),
         'date_aftereq': (lambda x, y: x is not None and y is not None and x <= y, datetime),
         'date_beforeq': (lambda x, y: x is not None and y is not None and x >= y, datetime),
         'after': (lambda x, y: x is not None and y is not None and x.day == y.day and x.start_time >= y.end_time, OccurenceDTO),
         'before': (lambda x, y: x is not None and y is not None and x.day == y.day and y.start_time >= x.end_time, OccurenceDTO),#symmteric?
         'intersect': (lambda x, y: x is not None and y is not None and x.day == y.day and (y.start_time <= x.start_time < y.end_time or
                                                                                            x.start_time <= y.start_time < x.end_time) , OccurenceDTO),
         'contains': (lambda x, y: x is not None and y is not None and y in x, String),
         'contained': (lambda x, y: x is not None and y is not None and x in y, String),
         'startswith': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         'initof': (lambda x, y: x is not None and y is not None and x.startswith(y), String),
         }

clss = [(CourseDTO, Course), (MultiCourseDTO, MultiCourse),
       (OccurenceDTO, Occurence), (LecturerDTO, Lecturer),
        (PhoneDTO, Phone), (ExamDTO, Exam), ]

init2cls = {cl.__tablename__[:3]: (dto_cl, cl) for dto_cl, cl in clss}

#very very stupid
manys_preds = {k for _, cl in init2cls.values() for k, v in vars(cl).items() if k[0] != '_' and vars(v).get('type') == list}

name2cls = {cl.__tablename__: (dto_cl, cl) for dto_cl, cl in clss}

name2dto = {cl.__tablename__: dto_cl for dto_cl, cl in clss}

dto2name = {dto: k for k, dto in name2dto.iteritems()}


pred2type = dict(start_time='hour',
                 end_time='hour',
                 full_start_time='time',
                 full_end_time='time',
                 department='department',
                 faculty='faculty',
                 semsester='semsester',
                 kind='kind',
                 day='day',
                 building='building',
                 office_building='building',
                 full_office='room',
                 full_place='room',
                 place='room_number',
                 office='room_number',
                 phone='phone_number',
                 fax='phone_number',
                 email='email',
                 title='title',
                 honor='honor',
                 semester='semester',
                 name='name',
                 multi_course_id='course_id'
                )
pred2type.update({k: dto for k, (dto, _) in name2cls.iteritems()})
pred2type.update({k+'s': dto for k, (dto, _) in name2cls.iteritems()})

type2convert = dict(hour=int,
                   time=lambda s: tuple(map(int, s.split(','))),
                   day=int,
                   semester=int)

course_comopsed_pred = {}
'''
multi_course_composed_pred = {'moed_a':lambda mc: mc.test.moed_a,
                 'moed_b':lambda mc: mc.test.moed_b,
                 'start_time':lambda mc: {c.start_time for c in mc.courses for occ in c.occurences},
                 'end_time':lambda mc: {c.start_time for c in mc.courses for occ in c.occurences},
                 'kind':lambda mc: {c.kind for c in mc.courses for occ in c.occurences},
                 'teachers':lambda mc: set.union(*(c.lecturers for c in mc.courses)),
                 'lecturer':lambda mc: set.union(*(c.lecturers for c in mc.courses if c.kind == 'lecture')),
                 'assistant':lambda mc: set.union(*(c.lecturers for c in mc.courses if c.kind == 'recitation')),
                 'building':lambda mc: {occ.building for c in mc.courses},
                 'place':lambda mc: {c.place for occ in c.occurences},                              
                }
'''

class DCS(object):
    span = ()
    is_func = False

class Expression(DCS):
    saved_res = None
    is_ent = False


class Entity(Expression):
    def __init__(self, id, type, span=[]):
        self.id = id
        self.type = type
        self.span = span
        is_ent = True

    def execute(self, db):
        table = db.type2table.get(self.type)
        if table is not None:
            return {table[self.id]}
        else:
            return {self.id}

    def __str__(self):
        return u'{}:{}'.format(dto2name.get(self.type, self.type), self.id)
    
    def copy(self, span):
        return Entity(self.id, self.type, span)    


class Intersect(Expression):
    def __init__(self, exp1, exp2, span=[]):
        self.exp1 = exp1
        self.exp2 = exp2
        self.type = exp1.type
        self.is_func = exp1.is_func and exp2.is_func
        self.span = span
        self.is_ent = exp1.is_ent or exp2.is_ent


        # assert exp1.type == exp2.type

    def execute(self, db):
        if self.saved_res:
            return self.saved_res
        exp1 = self.exp1
        exp2 = self.exp2
        if exp1.is_func and exp1.type not in db.type2table:
            if exp2.is_func and exp2.type not in db.type2table:
                return lambda x: exp1.execute(db)(x) and exp2.execute(db)(x)
            else:
                self.saved_res = {ent for ent in exp2.execute(db) if exp1.execute(db)(ent)}
                return self.saved_res
        elif exp2.is_func and exp2.type not in db.type2table:
            self.saved_res = {ent for ent in exp1.execute(db) if exp2.execute(db)(ent)}
            return self.saved_res
        self.saved_res = exp1.execute(db) & exp2.execute(db)
        return self.saved_res

    def __str__(self):
        return '({}&{})'.format(self.exp1, self.exp2)
    
    def copy(self, span):
        return Intersect(self.exp1, self.exp2)    

class BasePredicate(DCS):
    is_attr = False
    is_union = False
    is_rev = False
    is_lec = False
    unknown = False
    rtype = None
    ltype = None
    init = ''

    
class Predicate(BasePredicate):
    def __init__(self, pred, span=()):
        if type(pred) is Predicate:
            self.__dict__ = vars(pred)
            self.span = span
            return
        elif type(pred) is not str:
            self.unknown = True
            return
        self.pred = pred
        self.span = span
        func_type = funcs.get(pred)
        if func_type is not None:
            self.ltype = self.rtype = func_type[1]
            self.func = func_type[0]
            self.is_func = True
            return
        if pred[:4] == 'rev_':
            self.pred = pred = pred[4:]
            self.is_rev = True
        split_pred = pred.split('_')
        self.init = init = split_pred[0]
        self.pred = pred = '_'.join(split_pred[1:])
        ClassDTO, Class = init2cls.get(init, (CourseDTO, Course))
        ltype = pred2type.get(pred)
        if ltype is not None:
            if self.is_rev:
                self.rtype = ltype
                self.ltype = ClassDTO
                if pred in manys_preds:
                    self.unknown = True
            else:
                if pred in manys_preds:
                    self.is_union = True
                self.ltype = ltype
                self.rtype = ClassDTO
                
            self.is_attr = True
        else:
            self.unknown = True

    def __str__(self):
        return '{}{}_{}'.format('rev_' * self.is_rev, self.init, self.pred)
    
    def copy(self, span):
        return Predicate(self, span)


class Join(Expression):
    def __init__(self, pred, un, span=(), pred_span=(), is_bridge=False):
        self.un = un
        self.span = span
        self.is_bridge = is_bridge
        if isinstance(pred, str):
            self.pred = Predicate(pred, pred_span)
        else:
            self.pred = pred
        self.is_attr = self.pred.is_attr
        self.is_attr = self.pred.is_attr
        self.is_union = self.pred.is_union
        self.is_func = self.pred.is_func
        self.is_rev = self.pred.is_rev
        
        if self.pred.is_func:
            self.type = self.un.type
        else:
            self.type = self.pred.ltype
        if self.is_attr and not self.is_rev and not self.is_union:
            self.is_ent = self.un.is_ent

    def execute(self, db):#what a fucked function!!!!
        if self.saved_res:
            return self.saved_res
        assert not self.pred.unknown
        un = self.un
        pred = self.pred.pred
        table = db.type2table.get(self.type)
        if self.is_func:
            # reminder: funcs predicate are between same types!!
            # more convinient that func join of real db entity will return actual enities
            if table is not None:
                func = self.pred.func
                ents = un.execute(db)
                if not ents:
                    self.saved_res = set()
                    return self.saved_res
                self.saved_res = {c for c in table.values()
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
            if un.is_func and un.type not in db.type2table:
                self.saved_res = {ent for ent in table.values() if ents(getattr(ent, pred))}
                return self.saved_res
            else:
                self.saved_res = {ent for ent in table.values() if getattr(ent, pred) in ents}
                return self.saved_res
        elif self.is_attr:
            if self.is_union:
                ents = un.execute(db)
                if not ents:
                    self.saved_res = set()
                    return self.saved_res
                self.saved_res = set.union(*(set(getattr(ent, pred)) for ent in ents))
            else:    
                self.saved_res = {ent and getattr(ent, pred) for ent in un.execute(db)}
            return self.saved_res

    def __str__(self):
        return '({}.{})'.format(self.pred, self.un)
    
    def copy(self, span):
        return Join(self.pred.copy(span), self.un.copy(span), span)    

class LexEnt(Expression):
    def __init__(self, words, type, span=()):
        if not isinstance(words, list):
            words = list(words)
        #nltk seperate the 's
        try:
            i = words.index("'s") 
            if i > 0:
                del words[i]
                words[i -1 ] += "'s"
        except ValueError:
            pass
        self.pcapital = mean([w[0].isupper() for w in words])
        self.words = [word.lower() for word in words]
        self.pwords = None
        self.span = span
        self.type = type
        self.is_ent = True
    
    #def 
    
    def execute(self, db):
        if self.saved_res:
            return self.saved_res
        d = db.type2words_dict[self.type]
        for word in self.words:
            if not d:
                self.saved_res = set()
                return self.saved_res
            v = d.get(word)
            if v is None:
                self.saved_res = set()
                return self.saved_res
            s, d, p = v
        self.pwords = p
        self.saved_res = s
        return self.saved_res
    
    def __str__(self):
        return '{}@{}'.format(dto2name.get(self.type, self.type), ','.join(self.words))

class Aggregation(DCS):
    def __init__(self, exp=None, span=[], type=None):
        self.exp = exp
        self.span = span
        self.rtype = type
        self.is_ent = True
        
    def copy(self, span, exp=None):
        exp = type(self)(exp or self.exp, span)
        exp.rtype = self.rtype
        return exp


class Count(Aggregation):
    # TODO: handle mutiplicity
    def __init__(self, exp=None, span=[]):
        Aggregation.__init__(self, exp, span, None)
        self.type = 'count'
        
        

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
        self.type = rtype    
    
    def execute(self, db):
        ents = self.exp.execute(db)
        if not ents:
            return set()
        return {self.func(self.exp.execute(db), key=lambda c: self.attr(c) or self.ext_obj)}

    def __str__(self):
        return 'arg{}_{}{}'.format(func.__name__, self.exp)


class Earliest(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, OccurenceDTO, lambda x: x.start_time, inf, min)
    
    def __str__(self):
        return 'earliest{}'.format(self.exp)


class Latest(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, OccurenceDTO, lambda x: x.start_time, -inf, max)

    def __str__(self):
        return 'latest{}'.format(self.exp)

class EarliestMoedA(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, MultiCourseDTO, lambda x: x.exam.moed_a, future_time, min)
    
    def __str__(self):
        return 'earliest_moeda{}'.format(self.exp)


class LatestMoedA(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, MultiCourseDTO, lambda x: x.exam.moed_b, past_time, max)

    def __str__(self):
        return 'latest_moeda{}'.format(self.exp)

class EarliestMoedB(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, MultiCourseDTO, lambda x: x.exam.moed_b, future_time, min)
    
    def __str__(self):
        return 'earliest_moedb{}'.format(self.exp)


class LatestMoedB(Arg):
    def __init__(self, exp=None, span=[]):
        Arg.__init__(self, exp, span, MultiCourseDTO, lambda x: x.exam.moed_b, past_time, max)

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
ops = '&.:@'

def parse_dcs(exp):
    in_parents = exp[0] == '(' and exp[-1] == ')'
    match = aggregat_p.match(exp)
    is_agg = False
    if match:
        is_agg = match.start() == 0
        aggregat_name, = match.groups()
        aggregat = aggregats[aggregat_name]
        in_parents = exp[-1] == ')'
    char_in_parents = [False]*len(exp)
    counter = 0
    for op in ops:    
        for i, c in enumerate(exp):
            if c == '(':
                counter += 1
            elif c == ')':
                counter -= 1
            elif counter == 0:
                if c in '&.:@':
                    in_parents = False
                else:
                    continue
                if c != op:
                    continue
                if c == '&':
                    return Intersect(parse_dcs(exp[:i]), parse_dcs(exp[i + 1:]))
                elif c == '.':
                    return Join(exp[:i], parse_dcs(exp[i + 1:]))
                elif c == ':':
                    type = name2dto.get(exp[:i], exp[:i])
                    func = type2convert.get(type)
                    id = func(exp[i+1:]) if func is not None else exp[i+1:]
                    return Entity(id, type)
                elif c == '@':
                    type = name2dto.get(exp[:i], exp[:i])
                    words = exp[i+1:].split(',')
                    return LexEnt(words, type)
            
        assert counter >= 0
    if in_parents:
        if is_agg:
            return aggregat(parse_dcs(exp[len(aggregat_name)+1: -1]))
        return parse_dcs(exp[1:-1])
    assert False
