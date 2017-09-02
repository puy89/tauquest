import csv

import numpy as np

from db.db import db_instance
from db.entities import Course, Lecturer
from training.lexicon import Lexicon
from training.questions_answers_trainer import QuestionsAnswersTrainer


class DBCache(object):
    def __init__(self):
        self.session = db_instance.session
        self.courses = {c.id: c for c in self.session.query(Course)}
        self.lecturers = {l.id: l for l in self.session.query(Lecturer)}


def load_dataset():
    with open('files/questions-answers.csv') as f:
        r = csv.reader(f)
        questions, answers = np.array([(row[0], set(map(unicode, row[1:next(i for i, cell in enumerate(row) if cell == '')]))) for row in r]).T
        return questions, answers


def pretty_print_result(question, result):
    print(question)
    for r in result:
        if isinstance(r, Course):
            print(u"\t{0}".format(r.id))
        elif isinstance(r, Lecturer):
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
