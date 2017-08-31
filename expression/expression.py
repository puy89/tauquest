import re
from sqlalchemy import Integer, String, Unicode
from db.entities import Course
from db.entities import Lecturer

funcs = {'<': (lambda x, y: x is not None and y is not None and x < y, Integer),
         '>': (lambda x, y: x is not None and y is not None and x > y, Integer),
         '<=': (lambda x, y: x is not None and y is not None and x <= y, Integer),
         '>=': (lambda x, y: x is not None and y is not None and x >= y, Integer),
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


        # assert exp1.type == exp2.type

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


class Predicate(object):
    def __init__(self, pred, span=()):
        self.pred = pred
        self.span = span
        self.is_attr = False
        self.is_db_join = False
        self.is_func = False
        self.is_rev = False
        self.unknown = False
        if pred == 'teach':
            self.ltype = Course
            self.rtype = Lecturer
            self.is_db_join = True
            return

        if pred[:4] == 'rev_':
            self.pred = pred = pred[4:]
            self.is_rev = True
        attr = vars(Course).get(pred)
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
            attr = vars(Lecturer).get(pred)
            if attr is not None:
                if self.is_rev:
                    self.rtype = type(attr.type)
                    self.ltype = Lecturer
                else:
                    self.rtype = Lecturer
                    self.ltype = type(attr.type)
                self.is_attr = True
            else:
                func = funcs.get(pred)
                if func is not None:
                    self.ltype = self.rtype = func[1]
                    self.is_func = True
                else:
                    self.unknown = True

    def __str__(self):
        return '{}{}'.format('rev_' * self.is_rev, self.pred)


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

    def execute(self, db):
        un = self.un
        pred = self.pred.pred
        if self.is_func:
            if self.un.is_func:
                pass
                # TODO bom
            else:
                func = funcs[pred][0]
                ents = un.execute(db)
                return lambda x: any(func(x, ent) for ent in ents)
        elif self.is_rev:
            ents = un.execute(db)
            if un.is_func:
                if self.type == Course:
                    return {ent for ent in db.courses.values() if ents(getattr(ent, pred))}
                if self.type == Lecturer:
                    return {ent for ent in db.lecturers.values() if ents(getattr(ent, pred))}
            else:
                if self.type == Course:
                    return {ent for ent in db.courses.values() if getattr(ent, pred) in ents}
                if self.type == Lecturer:
                    return {ent for ent in db.lecturers.values() if getattr(ent, pred) in ents}
        elif self.is_attr:
            return {getattr(ent, pred) for ent in un.execute(db)}
        elif self.is_db_join:
            # TODO: other joins?
            return {c for ent in un.execute(db) for c in db.courses.values() if c.lecturer_id == ent.id}

    def __str__(self):
        return '({}.{})'.format(self.pred, self.un)


class Aggregation(object):
    def __init__(self, exp=None, span=[]):
        self.exp = exp
        self.span = span
        self.is_func = False


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
        return Lectures()
    return exp
