import csv

import numpy as np

from db.db import db_instance
from db.entities import Course, Lecturer, CourseDTO, LecturerDTO
from training.lexicon import Lexicon
from training.questions_answers_trainer import QuestionsAnswersTrainer
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x

def create_words_dict(ents):
    cache = {}
    def create_words_dict(ents, path=()):
        if len({ent.name for ent in ents}) == 1:
            return
        d = {}
        for ent in ents:
            for word in ent.name.split():
                if word not in path:
                    k = tuple(sorted(path + (word,)))
                    old_d = cache.get(k)
                    if old_d is not None:
                        d[word] = old_d
                    else:
                        d.setdefault(word, set()).add(ent)
        for word, v in d.items():
            if type(v) is set:
                k = tuple(sorted(path + (word,)))
                new_d = create_words_dict(v, path+(word,))
                cache[k] = d[word] = v, new_d
        return d
    return create_words_dict(ents)

    

class DBCache(object):
    def __init__(self):
        self.session = db_instance.session
        self.courses = {c.id: CourseDTO(c) for c in self.session.query(Course)}
        self.lecturers = {l.id: LecturerDTO(l) for l in self.session.query(Lecturer)}
        self.honors = {l.honor for l in self.lecturers.values() if l.honor is not None}
        self.kinds = {l.kind for l in self.courses.values() if l.kind is not None}
        self.session.close()
        self.name2courses = {}
        self.courses_words_dict = create_words_dict(self.courses.values())
        self.lecturers_words_dict = create_words_dict(self.lecturers.values())


def load_dataset():
    with open('files/questions-answers.csv') as f:
        r = csv.reader(f)
        questions, answers = np.array([(row[0], set(map(unicode, row[1:next(i for i, cell in enumerate(row) if cell == '')]))) for row in r]).T
        return questions, answers


def pretty_print_result(question, result):
    print(question)
    for r in result:
        if isinstance(r, CourseDTO):
            print(u"\t{0}".format(r.id))
        elif isinstance(r, LecturerDTO):
            print(u"\t{0}".format(r.id))
        else:
            print(u"\t{0}".format(r))

def main():
    db_cache = DBCache()
    lexicon = Lexicon()
    lexicon.update_lexicon(db_cache)
    questions, answers = load_dataset()
    trainer = QuestionsAnswersTrainer(db_cache, lexicon.lexicon)

    theta = trainer.train(questions, answers, iters=100)
    print(theta)

    pretty_print_result(questions[0], trainer.eval(questions[0], theta))
    pretty_print_result(questions[1], trainer.eval(questions[1], theta))
    pretty_print_result(questions[2], trainer.eval(questions[2], theta))
    pretty_print_result(questions[3], trainer.eval(questions[3], theta))
    pretty_print_result(questions[4], trainer.eval(questions[4], theta))


if __name__ == '__main__':
    main()
