from datetime import datetime
import numpy as np
from dto.dtos import MultiCourseDTO, LecturerDTO
from questions_parser import QuestionsParser
from training.feature_extrector import NUMBER_OF_FEATURES
from expression.expression import Entity
import sys
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x
sys.stdout = open('log', 'a')
    
class QuestionsAnswersTrainer:
    def __init__(self, db, lexicon):
        self._db = db
        self._lexicon = lexicon
        self._questions_parser = QuestionsParser(db, self._lexicon)
        self.theta = None

    def adagrad(self, gradient, x0, step, iterations, adaptive=False):
        eps = 1e-06
        ANNEAL_EVERY = 20000
        x = x0
        expcost = None
        begin = datetime.now()
        G = np.zeros_like(x0, float)
        for iter in tqdm(range(0 + 1, iterations + 1)):
            # Don't forget to apply the postprocessing after every iteration!
            # You might want to print the progress every few iterations.
            cost = None
            ### YOUR CODE HERE
            grad = gradient(x)
            if grad is None:
                print 'gradient is None'
                continue
            G += grad ** 2
            direct = step * grad
            if adaptive:
                direct /= (np.sqrt(G) + eps)
            x -= direct
            ### END YOUR CODE


            if iter % ANNEAL_EVERY == 0:
                step *= 0.5

        return x

    @staticmethod
    def is_right_answer(exp, db, expected_answers):
        results = exp.execute(db)
        if results == expected_answers:
            return True
        if type(results) != set:
            return False
        if exp.type == MultiCourseDTO:
            return {course.name for course in results} == expected_answers

        elif exp.type == LecturerDTO:
            return {lecturer.name for lecturer in results} == expected_answers
        else:
            return set(map(unicode, results)) == expected_answers

        return False

    
    def train(self, quests, ans, k=1000, iters=None):
        def gradient(theta):
            i = np.random.randint(0, len(quests))
            exps = self._questions_parser.parse_sent(quests[i], theta, k)
            if len(exps) == 0:
                print quests[i], 'no derivations'
                return None
            exps, feats = np.array(exps).T
            feats = np.array([feat for feat in feats], float)
            ps = np.exp(feats.dot(theta))
            agree = [self.is_right_answer(exp, self._db, ans[i]) for exp in exps]
            if not any(agree):
                print quests[i], 'no good derivations'
                return None
            unnormed = ps * agree
            qs = unnormed / unnormed.sum()
            grad = feats.T.dot(qs - ps)
            assert not np.isnan(grad).any()
            return -grad

        iters = iters or len(quests)
        self.theta = self.adagrad(gradient, np.zeros(NUMBER_OF_FEATURES) if self.theta is None else self.theta, 0.01, iters)
        return self.theta

    def eval(self, question, theta=None, k=100):
        theta = self.theta if theta is None else theta
        exps, feats = np.array(self._questions_parser.parse_sent(question, theta, k)).T
        feats = np.array([feat for feat in feats], float)
        return exps[0].execute(self._db)
    
    def get_exps(self, question, theta=None, k=100):
        theta = self.theta if theta is None else theta
        exps_feats = np.array(self._questions_parser.parse_sent(question, theta, k)).T
        if len(exps_feats):
            exps, _feats = exps_feats
            return exps
        return [Entity('error', 'error')]
        
