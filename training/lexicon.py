from expression.expression import Predicate, Join, Entity, aggregats, Integer, Unicode, DCS


class Lexicon:

    def __init__(self):
        self._lexicon = \
            {
                'who': ['cou_lecturers', 'pho_lecturer'],
                'whom': ['cou_lecturers', 'pho_lecturer'],
                'teach': ['lec_courses', 'cou_lecturers'],
                'course': ['lec_courses', 'cou_lecturers', 'rev_mul_department', 'rev_mul_faculty'],
                'taught': ['lec_courses'],
                'lecturer': ['cou_lecturers', 'lec_courses'],
                'department': ['mul_department', 'mul_faculty'],
                'faculty': ['mul_faculty', 'mul_department'],
                'when': ['occ_day', 'occ_start_time', 'mul_semester'],# add full time
                'it': [],
                'what': [],
                'which': [],
                'there': [],
                'is': [],
                'am': [],
                'are': [],
                'the': [],
                'do': [],
                'does': [],
                'by': [],
                'pm': [],
                'of': ['rev_mul_department', 'rev_mul_faculty'],
                'about': [],
                'day': ['occ_day'],
                'in': ['occ_full_place', 'occ_place', 'mul_semester', 'occ_building', 'mul_department', 'mul_faculty', 'lec_full_office', 'lec_office_building'],
                'on': ['occ_day', 'occ_place', 'mul_semester', 'occ_building', 'mul_department', 'mul_faculty'],
                'at': ['occ_full_start_time', 'occ_start_time', 'occ_full_end_time', 'occ_end_time'],
                "'s": ['cou_lecturers', 'lec_courses', 'rev_mul_department', 'rev_mul_faculty'],
                'email': ['lec_email'],
                'address': ['lec_email'],
                'phone': ['lec_phones', 'pho_phone'],
                'number': ['lec_phones', 'pho_phone', 'lec_fax', 'occ_place', 'mul_id'],
                'room': ['occ_full_place', 'lec_full_office', 'lec_office', 'occ_place'],
                'office': ['lec_full_office'],
                'where': ['occ_full_place', 'lec_full_office', 'occ_place', 'occ_building', 'lec_office', 'lec_office_building'],
                'locate': ['occ_full_place', 'lec_full_office', 'occ_place', 'occ_building', 'lec_office', 'lec_office_building'],
                'location': ['occ_full_place', 'lec_full_office', 'occ_place', 'occ_building', 'lec_office', 'lec_office_building'],
                'building': ['occ_building', 'lec_office_building', 'occ_place', 'lec_office'],
                'place': ['occ_full_place', 'lec_full_office', 'occ_place'],  # TODO: change place to room, add full adress
                'semester': ['occ_semester'],
                'kind': ['cou_kind'],
                'end': ['occ_full_end_time'],
                'start': ['occ_full_start_time', 'occ_start_time'],
                'begin': ['occ_full_start_time', 'occ_start_time'],
                'earliest': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'first': ['earliest', 'earliestmoeda', 'earliestmoedb'],
                'latest': ['latest', 'latestmoeda', 'latestmoedb'],
                'last': ['latest', 'latestmoeda', 'latestmoedb'],
                'test': ['mul_exam', 'moed_a', 'moed_b'],
                'exam': ['mul_exam', 'moed_a', 'moed_b'],
                'examination': ['mul_exam', 'moed_a', 'moed_b'],
                'much': ['count'],
                'many': ['count'],
                'assitant': [Join('rev_lec_honor', Entity('recitation', 'honor'), is_bridge=True)],
                'sunday': [Entity(1, 'day')],
                'monday': [Entity(2, 'day')],
                'tuesday': [Entity(3, 'day')],
                'wednesday': [Entity(4, 'day')],
                'thursday': [Entity(5, 'day')],
                'friday': [Entity(6, 'day')],
                'saturday': [Entity(7, 'day')],
                'first': [Entity(1, 'semeter')],
                'winter': [Entity(1, 'semeter')],
                'second': [Entity(2, 'semeter')],
                'spring': [Entity(2, 'semeter')],
                'collide': ['intersect'],
                'after': ['after', '>', '>=', 'hour>', 'hour>='],
                'before': ['before', 'hour<', 'hour<='],
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
                            if parsed_opts[-1].is_attr and not parsed_opts[-1].is_rev:
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
                self._lexicon[honor] = [Join('rev_lec_honor', Entity(honor, 'honor'), is_bridge=True)]
                if honor[-1] != '.':
                    self._lexicon[honor+'.'] = [Join('rev_lec_honor', Entity(honor, 'honor'), is_bridge=True)]
                elif honor[-1] == '.':
                    self._lexicon[honor[:-1]] = [Join('rev_lec_honor', Entity(honor, 'honor'), is_bridge=True)]
                
        for kind in db.kinds:
            self._lexicon[kind] = [Join('rev_cou_kind', Entity(kind, 'kind'), is_bridge=True)]
            
            

    @property
    def lexicon(self):
        return self._lexicon