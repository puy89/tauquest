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
        questions, answers = np.array([(row[0], set(row[1:])) for row in r]).T
        return questions, answers


def main():
    db_cache = DBCache()
    lexicon = Lexicon()
    lexicon.update_lexicon(db_cache)
    questions, answers = load_dataset()
    trainer = QuestionsAnswersTrainer(db_cache, lexicon._lexicon)

    theta = trainer.train(questions, answers)
    print(theta)

    print(trainer.eval(questions[0], theta))
    print(trainer.eval(questions[1], theta))


if __name__ == '__main__':
    main()
