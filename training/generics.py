import numpy as np
import re
from expression.expression import parse_dcs
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x


generic_questions = [('What courses of {department} are on {day}?', '(rev_mul_department.department@{department})&(cou_multi_course.occ_course.rev_occ_day.day:{day})'),
                     ('what courses of {department} are after {course}?', '(rev_mul_department.department@{department})&(cou_multi_course.occ_course.after.cou_occurences.occ_courses.multi_course@{course})'),
                     ('what courses of {department} are before {course}?', '(rev_mul_department.department@{department})&(cou_multi_course.occ_course.before.cou_occurences.occ_courses.multi_course@{course})'),
                     ('who is the lecturer of {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('who is the lecturer of the course {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('who teaches the course {course}?',  'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('who teaches {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('what is the staff of course {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('what is the staff of {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('what is the staff of the course {course}?', 'cou_lecturers.mul_courses.multi_course@{course}'),
                     ('where is {course}?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('where is the class {course}?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('where is class {course}?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('where is {course} located?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('where is the course {course} located?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('where is course {course} located?', 'occ_full_place.cou_occurences.mul_courses.multi_course@{course}'),
                     ('what is the latest class of {department} on {day}?', 'cou_multi_course.occ_course.latest(cou_occurences.mul_courses.rev_mul_department.department@{department}&rev_occ_day.day:{day})'),
                     ('what courses collide with {course}?', 'cou_multi_course.occ_course.intersect.cou_occurences.mul_courses.multi_course@{course}'),
                     ('what courses collide with the recitation of {course}?', 'cou_multi_course.occ_course.intersect.(cou_occurences.mul_courses.multi_course@{course}&cou_occurences.rev_cou_kind.kind:recitation)'),
                     ('what courses collide with the course {course}?', 'cou_multi_course.occ_course.intersect.cou_occurences.mul_courses.multi_course@{course}'),
                     ('what courses collide with the recitation of the course {course}?', 'cou_multi_course.occ_course.intersect.(cou_occurences.mul_courses.multi_course@{course}&cou_occurences.rev_cou_kind.kind:recitation)')]


format_p = re.compile('\\{([a-z]+)\\}')

def find_department(db, size=1):
    sized = [k for k, (s, _, _) in db.departments_words_dict.iteritems() if len(s) == size]
    return sized[np.random.randint(0, len(sized))]

def find_course(db, size=5):
    failed = True
    while failed:
        failed = False
        d = db.multi_courses_words_dict
        s = [None]*(size + 1)
        words = []
        while len(s) > size:
            d_words = d.keys()
            
            word = d_words[np.random.randint(0, len(d_words))]
            s, d, _ = d[word]
            words.append(word)
            if not d:
                failed = len(s) > size
                break
    return ' '.join([word if np.random.random() > 0.9 else word.capitalize()
                     for word in words])
days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

day2num = {k: i for i, k in enumerate(days)}

def find_day(db):
    return np.random.randint(1, 7)


format2find = dict(day=find_day, course=find_course, department=find_department)


def create_sample_from_generics(generic_questions, db):
    questions = []
    answers = []
    for q, exp in tqdm(generic_questions):
        s = {}
        while not 1 <=len(s) < 500:
            formats = format_p.findall(q)
            kwargs = {f: format2find[f](db) for f in formats}
            s = parse_dcs(exp.format(**kwargs)).execute(db)
            day = kwargs.get('day')
            if day is not None:
                kwargs['day'] = days[day-1]
        questions.append(q.format(**kwargs))
        answers.append(s)
    return questions, answers