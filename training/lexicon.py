from expression.expression import Predicate, Join, Entity, aggregats, Integer, Unicode, DCS
import re

time_p = re.compile('([0-2][0-9]):([0-5][0-9])')

class Lexicon:

    def __init__(self):
        self._lexicon = \
            {
                'who': ['cou_lecturers'],
                'teach': ['lec_courses', 'cou_lecturers'],
                'taught': ['lec_courses', 'cou_lecturers'],
                'lecturer': ['cou_lecturers', 'lec_courses'],
                'department': ['mul_department', 'mul_faculty'],
                'faculty': ['mul_faculty', 'mul_department'],
                'when': ['occ_day', 'occ_start_time', 'mul_semester'],# add full time
                'day': ['occ_day'],
                'in': ['occ_place', 'mul_semester', 'occ_building', 'mul_department', 'mul_faculty'],
                'on': ['occ_day', 'occ_place', 'mul_semester', 'occ_building', 'mul_department', 'mul_faculty'],
                'at': ['occ_start_time'],
                'of': ['mul_department', 'mul_faculty'],
                "'s": ['mul_department', 'mul_faculty'],
                'email': ['lec_email'],
                'address': ['lec_email'],
                'phone': ['lec_phones'],
                'number': ['lec_phones', 'lec_fax', 'occ_place', 'mul_id'],
                'room': ['lec_office', 'occ_place'],
                'where': ['occ_place', 'occ_building', 'lec_office', 'lec_office_building'],
                'building': ['occ_building', 'lec_office_building', 'occ_place', 'lec_office'],
                'place': ['occ_place'],  # TODO: change place to room, add full adress
                'semester': ['occ_semester'],
                'kind': ['cou_kind'],
                'end': ['occ_end_time'],
                'start': ['occ_start_time'],
                'begin': ['occ_start_time'],
                'earliest': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'first': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'latest': ['latest', 'latestmoeda', 'latestmoedb'],
                'last': ['latest', 'latestmoeda', 'latestmoedb'],
                'test': ['mul_exam', 'moed_a', 'moed_b'],
                'exam': ['mul_exam', 'moed_a', 'moed_b'],
                'examination': ['mul_exam', 'moed_a', 'moed_b'],
                'much': ['count'],
                'many': ['count'],
                'sunday': [Entity(1, 'day')],
                'monday': [Entity(2, 'day')],
                'tuesday': [Entity(3, 'day')],
                'wednesday': [Entity(4, 'day')],
                'thursday': [Entity(5, 'day')],
                'friday': [Entity(6, 'day')],
                'saturday': [Entity(7, 'day')],
                'after': ['after', '>', '>='],
                'before': ['before', '<', '<='],
           }

    def update_lexicon(self, db):
        for keys, values in self._lexicon.items():
            parsed_opts = []
            for opt in values:
                if isinstance(opt, DCS):
                    parsed_opts.append(opt)
                else:
                    aggregat_cls = aggregats.get(opt)
                    if aggregat_cls is not None:
                        parsed_opts.append(aggregat_cls())
                    else:
                        pred = Predicate(opt)
                        if not pred.unknown:
                            parsed_opts.append(pred)
                            if parsed_opts[-1].is_attr:
                                rev_pred = Predicate('rev_' + opt)
                                if not rev_pred.unknown:
                                    parsed_opts.append(rev_pred)
                        elif type(opt) is int:
                            ent = Entity(opt, Integer)
                            parsed_opts.append(ent)
            self._lexicon[keys] = parsed_opts
        #primitive bridge
        for honor in db.honors:
            for lower in xrange(2):
                if lower:
                    honor = honor.lower()
                self._lexicon[honor] = [Join('rev_lec_honor', Entity(honor, Unicode))]
                if honor[-1] != '.':
                    self._lexicon[honor+'.'] = [Join('rev_lec_honor', Entity(honor, Unicode))]
                elif honor[-1] == '.':
                    self._lexicon[honor[:-1]] = [Join('rev_lec_honor', Entity(honor, Unicode))]
                
        for kind in db.kinds:
            self._lexicon[kind] = [Join('rev_cou_kind', Entity(kind, Unicode))]
            
            

    @property
    def lexicon(self):
        return self._lexicon