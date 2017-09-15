from __future__ import division
import csv
import numpy as np
import re

from db.db import db_instance
from db.entities import Lecturer, MultiCourse
from dto.dtos import CourseDTO, LecturerDTO, MultiCourseDTO, OccurenceDTO, PhoneDTO
from training.lexicon import Lexicon
from training.questions_answers_trainer import QuestionsAnswersTrainer

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x

puncts_p = re.compile('[&\\(\\)\\.\\,:\\?&]')

def clear(s):
    s = ''.join(puncts_p.split(s))
    s = s.replace('-', ' ').lower()
    return s
    
def create_words_dict(ents, func=lambda x: x, ordered=False):
    cache = {}
    def create_words_dict_rec(ents, path=()):
        if all(sorted(path) == sorted(clear(func(ent)).split()) for ent in ents):
            return None, 1
        d = {}
        p = 0
        for ent in ents:
            clean = clear(func(ent))
            words = clean.split()
            #remove '' entities
            if words:
                curr_p = len(path)/len(words)
                if curr_p > p:
                    p = curr_p
            for word in words:
                if word not in path:
                    if not ordered:
                        k = tuple(sorted(path + (word,)))
                        old_d = cache.get(k)
                        if old_d is not None:
                            d[word] = old_d
                        else:
                            d.setdefault(word, set()).add(ent)
                    elif ' '.join(path + (word,)) in clean:
                        d.setdefault(word, set()).add(ent)
                        
        for word, v in d.items():
            if type(v) is set:
                k = tuple(sorted(path + (word,)))
                new_d, new_p = create_words_dict_rec(v, path + (word,))
                if new_p == 1:
                    v = {ent for ent in v if sorted(path + (word,)) == sorted(clear(func(ent)).split())}
                cache[k] = d[word] = (v, new_d, new_p)
                
        return d, p

    return create_words_dict_rec(ents)[0]


class DBCache(object):
    def __init__(self):
        self.session = db_instance.session
        print 'extract information from db'
        # fetch multi courses
        print 'courses'
        self.multi_courses = {mc.id: MultiCourseDTO(mc) for mc in tqdm(self.session.query(MultiCourse))}
        # fetch lecturers
        print 'lecturers'
        self.lecturers = {l.id: LecturerDTO(l) for l in tqdm(self.session.query(Lecturer))}

        # close session
        self.session.close()
        print 'extract relation from db'
        # update courses
        self.courses = dict()
        for multi_course in self.multi_courses.values():
            multi_course.exam.update_exam(self.multi_courses)
            for course in multi_course.courses:
                self.courses[course.id] = course

        # update occurences
        self.occurences = dict()
        for course in self.courses.values():
            course.update_course(self.multi_courses)
            for occurence in course.occurences:
                self.occurences[occurence.id] = occurence
                occurence.update_occurence(self.courses)


        # update course objects for all lecturers
        for lecturer in self.lecturers.values():
            lecturer.update_courses(self.courses)
        self.phones = dict()
        for course in self.courses.values():
            for lecturer in course.lecturers:
                lecturer.update_courses(self.courses)
        for lecturer in self.lecturers.values():
            for phone in lecturer.phones:
                phone.update_phone(self.lecturers)
                self.phones[phone.id] = phone
                    
        print 'extract strings from db'
        self.honors = {l.honor for l in self.lecturers.values() if l.honor is not None}
        self.kinds = {l.kind for l in self.courses.values() if l.kind is not None}
        print 'creating words trees'
        self.multi_courses_words_dict = create_words_dict(self.multi_courses.values(), lambda x: x.name, True)
        self.lecturers_words_dict = create_words_dict(self.lecturers.values(), lambda x: x.name)
        self.buildings_words_dict = create_words_dict(
            {l.office_building for l in self.lecturers.values() if l.office_building is not None} |
            {occ.building for c in self.courses.values() for occ in c.occurences if occ.building is not None})
        self.departments_words_dict = create_words_dict(
            {c.department for c in self.multi_courses.values() if c.department is not None})
        self.faculties_words_dict = create_words_dict(
            {c.faculty for c in self.multi_courses.values() if c.faculty is not None})
        self.type2table = {MultiCourseDTO: self.multi_courses,
                           CourseDTO: self.courses,
                           OccurenceDTO: self.occurences,
                           LecturerDTO: self.lecturers,
                           PhoneDTO: self.phones}
        self.type2words_dict = {MultiCourseDTO: self.multi_courses_words_dict,
                                LecturerDTO: self.lecturers_words_dict,
                                'building': self.buildings_words_dict,
                                'department': self.departments_words_dict,
                                'faculty': self.faculties_words_dict}
        print 'db is ready'

        
        

def load_dataset():
    with open('files/questions-answers.csv') as f:
        r = csv.reader(f)
        questions = []
        paraphrases = []
        answers = []
        r.next()#next titles row
        for row in r:
            paraphrases.append(row[0])
            questions.append(row[1])
            anss = row[2].split('#')
            if len(anss) > 1:
                answers.append(set(map(unicode, anss)))
            else:
                answers.append({unicode(cell) for cell in row[2:next((i for i, cell in enumerate(row)
                                                                      if i > 0 and cell == ''), None)]})
        return questions+paraphrases, answers*2


def pretty_print_result(question, result):
    print(question)
    for r in result:
        if isinstance(r, CourseDTO):
            print(u"\t{0}".format(r.id))
        elif isinstance(r, LecturerDTO):
            print(u"\t{0}".format(r.id))
        else:
            print(u"\t{0}".format(r))


def main(iters=100):
    db_cache = DBCache()
    lexicon = Lexicon()
    lexicon.update_lexicon(db_cache)
    questions, answers = load_dataset()
    trainer = QuestionsAnswersTrainer(db_cache, lexicon.lexicon)

    theta = trainer.train(questions, answers, iters=100)

    print("saving theta to file")
    np.save("files/theta", theta)


if __name__ == '__main__':
    main()
