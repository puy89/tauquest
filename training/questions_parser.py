import numpy as np
import nltk

from expression.expression import (Expression, Join, Intersect, Predicate, Aggregation,
                                   CourseDTO, LecturerDTO, LexEnt, Entity, Unicode, DCS, type2preds)
from training.feature_extrector import FeatureExtractor
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x



    


        

class QuestionsParser:

    def __init__(self, db, lexicon):
        self._db = db
        self._lexicon = lexicon
        self._feature_extractor = FeatureExtractor(db)

    def bridge(self, sent, exp):#stupid!!!!!!!!!!!!!
        return [(join, self._feature_extractor.extract_features(sent, join))
                for pred in type2preds[exp.type]
                #what sholud have the pred span??? should be? information will pass with structure?
                for join in [Join(pred.copy(exp.span), exp, span=exp.span)]]


    def parse_sent(self, sent, theta, k=10):
        sent = nltk.pos_tag(nltk.word_tokenize(sent))
        words = np.array(sent)[:, 0]
        n = len(sent)
        span_exps = {}
        for i, (w, pos) in enumerate(sent):
            terms = self._lexicon.get(w.replace('-', ' '))
            span_exps[i, i] = []
            if terms is not None:
                for term in terms:
                    if isinstance(terms[0], DCS):
                        span_exps[i, i].append((term.copy((i, i)), None))
            else:
                #span_exps[i, i].append((Entity(w, Unicode, (i, i)), None))
                exp = LexEnt([w], CourseDTO, (i, i) )
                if 0 < len(exp.execute(self._db)) < 1000: 
                    span_exps[i, i].append((exp, None))
                exp = LexEnt([w], LecturerDTO, (i, i))
                if 0 < len(exp.execute(self._db)) < 1000: 
                    span_exps[i, i].append((exp, None))
                
                
        for l in xrange(1, n):
            self._db.l = l
            for i in xrange(0, n - l):
                j = i + l
                exp = LexEnt(words[i: j+1], CourseDTO, (i, j))
                if 0 < len(exp.execute(self._db)) < 1000: #1000 is a lot!!!!
                    span_exps[i, j] = [(exp, None)]
                exp = LexEnt(words[i: j+1], LecturerDTO, (i, j))
                if 0 < len(exp.execute(self._db)) < 1000: #1000 is a lot!!!!
                    span_exps[i, j] = [(exp, None)]
        #after for: clear short span contained in probably good names?
        for l in xrange(1, n):
            self._db.l = l
            for i in xrange(0, n - l):
                j = i + l
                exps = span_exps.get((i, j), [])
                for m in xrange(i, j):
                    for h in xrange(m + 1, j + 1):
                        if not (len(span_exps[i, m]) and len(span_exps[h, j])):
                            continue
                        for left, _ in span_exps[i, m]:
                            for right, _ in span_exps[h, j]:
                                if isinstance(left, Predicate):
                                    if isinstance(right, Expression) and right.type == left.rtype and not (
                                                left.is_func and right.is_func):
                                        exp = Join(left, right, (i, j), (i, m))
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                elif isinstance(left, Expression):
                                    if isinstance(right, Predicate) and left.type == right.rtype and not (
                                                left.is_func and right.is_func):
                                        exp = Join(right, left, (i, j), (m + 1, j))
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                    elif isinstance(right, Expression):
                                        if right.type == left.type:
                                            exp = Intersect(right, left, (i, j))
                                            exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                    elif isinstance(right, Aggregation) and right.exp is None:
                                        if left.rtype is None or left.rtype == left.type:
                                            exp = right.copy((i, j), left)
                                            exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                elif isinstance(left, Aggregation) and left.exp is None:
                                    if isinstance(right, Expression) and (left.rtype is None or left.rtype == right.type):
                                        exp = left.copy((i, j), right)
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                        # if exp is not None:
                #bridge
                #exps.extend([join for exp, _ in exps if isinstance(exp, Expression) for join in self.bridge(sent, exp)])
                exps.sort(key=lambda (exp, feats): feats.dot(theta) if feats is not None else np.inf)
                span_exps[i, j] = exps[-k:]
        return span_exps[0, n - 1]
