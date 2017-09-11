from datetime import datetime
import numpy as np
from dto.dtos import CourseDTO, LecturerDTO
from questions_parser import QuestionsParser
from training.feature_extrector import NUMBER_OF_FEATURES


class QuestionsAnswersTrainer:
    def __init__(self, db, lexicon):
        self._db = db
        self._lexicon = lexicon
        self._questions_parser = QuestionsParser(db, self._lexicon)

    def adagrad(self, gradient, x0, step, iterations, PRINT_EVERY=10):
        eps = 1e-06
        ANNEAL_EVERY = 20000
        x = x0
        expcost = None
        begin = datetime.now()
        G = np.zeros_like(x0, float)
        for iter in xrange(0 + 1, iterations + 1):
            # Don't forget to apply the postprocessing after every iteration!
            # You might want to print the progress every few iterations.
            cost = None
            ### YOUR CODE HERE
            grad = gradient(x)
            G += grad ** 2
            x -= step * grad / (np.sqrt(G) + eps)
            ### END YOUR CODE


            if iter % ANNEAL_EVERY == 0:
                step *= 0.5

        return x

    @staticmethod
    def is_write_answer(exp, db, expected_answers):
        results = exp.execute(db)

        if len(results) == 0:
            return False

        if isinstance(next(iter(results)), CourseDTO):
            return {course.name for course in results} == expected_answers

        elif isinstance(next(iter(results)), LecturerDTO):
            return {lecturer.name for lecturer in results} == expected_answers

        else:
            return {res for res in results} == expected_answers

        return False

    def train(self, quests, ans, k=100, iters=None):
        def gradient(theta):
            i = np.random.randint(0, len(quests))
            exps, feats = np.array(self._questions_parser.parse_sent(quests[i], theta, k)).T
            feats = np.array([feat for feat in feats], float)
            ps = np.exp(feats.dot(theta))
            agree = [self.is_write_answer(exp, self._db, ans[i]) for exp in exps]
            unnormed = ps * agree
            if unnormed.sum() == 0:
                qs = 0
            else:
                qs = unnormed / unnormed.sum()
            return feats.T.dot(qs - ps)

        iters = iters or len(quests)
        return self.adagrad(gradient, np.zeros(NUMBER_OF_FEATURES), 0.01, iters)

    def eval(self, question, theta, k=100):
        exps, feats = np.array(self._questions_parser.parse_sent(question, theta, k)).T
        feats = np.array([feat for feat in feats], float)
        return exps[0].execute(self._db)
