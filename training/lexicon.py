from db.entities import Course, Lecturer
from expression.expression import Predicate, Join, Entity, aggregats, Integer, Unicode


class Lexicon:

    def __init__(self):
        self._lexicon = \
            {
                'who': ['lecturer'],
                'what': ['teach', 'email'],
                'teach': ['lecturer', 'teach'],
                'taught': ['lecturer', 'teach'],
                'lecturer': ['lecturer', 'teach'],
                'department': ['department', 'faculty'],
                'faculty': ['faculty', 'department'],
                'when': ['day', 'start_time', 'semester'],# add full time
                'day': ['day'],
                'in': ['start_time', 'place', 'semester', 'building', 'department', 'faculty'],
                'of': ['start_time', 'place', 'semester', 'building', 'department', 'faculty'],
                'email': ['email'],
                'address': ['email'],
                'phone': ['phone'],
                'number': ['phone', 'fax', 'place', 'id'],
                'room': ['place'],
                'where': ['place', 'building', 'office'],
                'place': ['place'],  # TODO: change place to room, add full adress
                'semester': ['semester'],
                'kind': ['kind'],
                'end': ['end_time'],
                'start': ['start_time'],
                'begin': ['start_time'],
                'earliest': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'first': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'latest': ['latest', 'latestmoeda', 'latestmoedb'],
                'last': ['latest', 'latestmoeda', 'latestmoedb'],
                'test': ['moed_a', 'moed_b'],
                'exam': ['moed_a', 'moed_b'],
                'examination': ['moed_a', 'moed_b'],
                'much': ['count'],
                'many': ['count'],
                'sunday': [1],
                'monday': [2],
                'tuesday': [3],
                'wednesday': [4],
                'thursday': [5],
                'friday': [6],
                'saturday': [7],
                'after': ['>', '>='],
                'before': ['<', '<='],
           }

    def update_lexicon(self, db):
        for keys, values in self._lexicon.items():
            parsed_opts = []
            for opt in values:
                aggregat_cls = aggregats.get(opt)
                if aggregat_cls is not None:
                    parsed_opts.append(aggregat_cls())
                else:
                    pred = Predicate(opt)
                    if not pred.unknown:
                        parsed_opts.append(pred)
                        if parsed_opts[-1].is_attr:
                            parsed_opts.append(Predicate('rev_' + opt))
                    elif type(opt) is int:
                        ent = Entity(opt, Integer)
                        parsed_opts.append(ent)
            self._lexicon[keys] = parsed_opts
        #primitive bridge
        for honor in db.honors:
            for lower in xrange(2):
                if lower:
                    honor = honor.lower()
                self._lexicon[honor] = [Join('rev_honor', Entity(honor, Unicode))]
                if honor[-1] != '.':
                    self._lexicon[honor+'.'] = [Join('rev_honor', Entity(honor, Unicode))]
                elif honor[-1] == '.':
                    self._lexicon[honor[:-1]] = [Join('rev_honor', Entity(honor, Unicode))]
                
        for kind in db.kinds:
            self._lexicon[kind] = [Join('rev_kind', Entity(kind, Unicode))]
            

    @property
    def lexicon(self):
        return self._lexicon