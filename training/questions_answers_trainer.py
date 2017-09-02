from datetime import datetime
import numpy as np
from questions_parser import QuestionsParser

N = 2000


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
    def is_write_answer(exp, db, answer):
        results = exp.execute(db)
        for result in results:
            # trick - we don't know the type of object that is returned
            # and therefore we iterate over all its class fields
            for property, value in vars(result).iteritems():
                if value in answer:
                    return True

        return False

    def train(self, quests, ans, k=100, iters=None):
        def gradient(theta):
            i = np.random.randint(0, len(quests))
            exps, feats = np.array(self._questions_parser.parse_sent(quests[i], theta, k)).T
            feats = np.array([feat for feat in feats], float)
            ps = np.exp(feats.dot(theta))
            agree = [self.is_write_answer(exp, self._db, ans[i]) for exp in exps]
            assert any(agree)
            unnormed = ps * agree
            qs = unnormed / unnormed.sum()
            return feats.T.dot(qs - ps)

        iters = iters or len(quests)
        return self.adagrad(gradient, np.zeros(N), 0.01, iters)

    def eval(self, question, theta, k=100):
        exps, feats = np.array(self._questions_parser.parse_sent(question, theta, k)).T
        feats = np.array([feat for feat in feats], float)
        return [exp.execute(self._db) for exp in exps]
