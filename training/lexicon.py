from db.entities import Course, Lecturer
from expression.expression import Predicate, Entity, aggregats, Integer


class Lexicon:

    def __init__(self):
        self._lexicon = \
            {
                'who': ['lecturer'],
                'what': ['teach', 'email'],
                'teach': ['lecturer', 'teach'],
                'taught': ['lecturer', 'teach'],
                'lecturer': ['lecturer', 'teach'],
                'when': ['day', 'start_time', 'semester'],# add full time
                'day': ['day'],
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
                'much': ['count'],
                'sunday': [0],
                'monday': [1],
                'tuesday': [2],
                'wednesday': [3],
                'thursday': [4],
                'friday': [5],
                'saturday': [6],
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
                        parsed_opts.append(Entity(opt, Integer))                        

            self._lexicon[keys] = parsed_opts
        for course in db.courses.values():
            self._lexicon.setdefault(course.name, []).append(Entity(course.id, Course))
            self._lexicon.setdefault(course.name.lower(), []).append(Entity(course.id, Course))
        for lecturer in db.lecturers.values():
            if lecturer.name:  # not created when created courses table
                self._lexicon.setdefault(lecturer.name, []).append(Entity(lecturer.id, Lecturer))
                self._lexicon.setdefault(lecturer.name.lower(), []).append(Entity(lecturer.id, Lecturer))


                # TODO: add english name of lecturers

    @property
    def lexicon(self):
        return self._lexicon