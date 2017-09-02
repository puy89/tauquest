import numpy as np
import nltk

from expression.expression import (Expression, Join, Intersect, Predicate, Aggregation, Entity, String)
from training.feature_extrector import FeatureExtractor


class QuestionsParser:

    def __init__(self, db, lexicon):
        self._db = db
        self._lexicon = lexicon
        self._feature_extractor = FeatureExtractor(db)


    def parse_sent(self, sent, theta, k=10):
        # slowwwwwwwwww!!!!!
        for course in self._db.courses.values():
            if course.name in sent:
                sent = sent.replace(course.name, course.name.replace(' ', '-'))
        for lecturer in self._db.lecturers.values():
            if lecturer.name:  # not created when created courses table
                if lecturer.name in sent:
                    sent = sent.replace(lecturer.name, lecturer.name.replace(' ', '-'))
        sent = nltk.pos_tag(nltk.word_tokenize(sent))
        n = len(sent)
        span_exps = {}
        for i, (w, pos) in enumerate(sent):
            terms = self._lexicon.get(w.replace('-', ' '))
            span_exps[i, i] = []
            if terms is not None:
                if isinstance(terms[0], Expression):
                    for term in terms:
                        term.span = i, i
                        span_exps[i, i].append((term, None))
                elif isinstance(terms[0], Predicate):
                    for term in terms:
                        term.span = i, i
                        span_exps[i, i].append((term, None))
                elif isinstance(terms[0], Aggregation):
                    for term in terms:
                        term.span = i, i
                        span_exps[i, i].append((term, None))
            else:
                span_exps[i, i].append((Entity(w, String, (i, i)), None))
        for l in xrange(1, n):
            for i in xrange(0, n - l):
                j = i + l
                exps = []
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
                                    elif isinstance(right, Aggregation):
                                        exp = type(right)(left)
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                elif isinstance(left, Aggregation):
                                    if isinstance(right, Expression):
                                        exp = type(left)(right)
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                        # if exp is not None:

                exps.sort(key=lambda (exp, feats): feats.dot(theta) if feats is not None else np.inf)
                span_exps[i, j] = exps[-k:]
        return span_exps[0, n - 1]
