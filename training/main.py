import csv
import numpy as np
from db.entities import db_session, Course, Lecturer
from training.lexicon import Lexicon
from training.questions_answers_trainer import QuestionsAnswersTrainer


class DB(object):
    def __init__(self):
        self.s = db_session()
        self.courses = {c.id: c for c in self.s.query(Course)}
        self.lecturers = {l.id: l for l in self.s.query(Lecturer)}


def load_dataset():
    with open('files/questions-answers.csv') as f:
        r = csv.reader(f)
        questions, answers = np.array([(row[0], set(row[1:])) for row in r]).T
        return questions, answers


def main():
    db = DB()
    lexicon = Lexicon()
    lexicon.update_lexicon(db)
    questions, answers = load_dataset()
    trainer = QuestionsAnswersTrainer(db)

    trainer.train(questions, answers, lexicon._lexicon)


if __name__ == '__main__':
    main()
