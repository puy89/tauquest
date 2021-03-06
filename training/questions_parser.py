import numpy as np
import nltk

from expression.expression import (Expression, Join, Intersect, Predicate, Aggregation, OccurenceDTO, MultiCourseDTO,
                                   CourseDTO, LecturerDTO, LexEnt, Entity, Unicode, DCS, BasePredicate)
from training.feature_extrector import FeatureExtractor
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x

import re


time_p = re.compile('([0-2][0-9])(:([0-5][0-9]))?')
email_p = re.compile('([a-z0-9A-Z_]+@[a-z0-9A-Z_]+\\.[a-z0-9A-Z_]+(\\.[a-z0-9A-Z_]+)?(\\.[a-z0-9A-Z_]+)?)')
phone_p = re.compile('([0-9]{2})\\-?([0-9]{7})')
course_id_p = re.compile('([0-9]{4}\\-[0-9]{4})')


course_bridge_dict = {OccurenceDTO: ([Predicate('occ_course'), Predicate('cou_multi_course')], True),
               MultiCourseDTO: ([Predicate('mul_courses'), Predicate('cou_occurences')], True),
               CourseDTO: ([Predicate('cou_multi_course'), Predicate('cou_occurences')], False)}

bridge_dict = {'department': ([Predicate('rev_mul_department')], False),
               'faculty': ([Predicate('rev_mul_faculty')], False)}

        

class QuestionsParser:

    def __init__(self, db, lexicon):
        self._db = db
        self._lexicon = lexicon
        self._feature_extractor = FeatureExtractor(db)

    def course_bridge(self, exp, span, sent):
        
        exps = []
        preds = course_bridge_dict.get(exp.type)
        if preds is None:
            return exps
        preds, recurrent = preds
        for pred in preds:
            join = Join(pred.copy(span), exp, span, is_bridge=True)
            if recurrent:
                exp = join
            exps.append((join, self._feature_extractor.extract_features(sent, join)))
        return exps    

    def parse_regexp(self, time):
        match = time_p.match(time)
        if match:
            if len(time) <= 5:
                t = time_p.findall(time)[0]
                h = int(t[0])
                m = int(t[2] or 0)
                return Entity(h*100+m, 'hour')
        match = phone_p.match(time)
        if match:
            pre, phone = match.groups()
            return Entity(pre+'-'+phone, 'phone')
        match = email_p.match(time)
        if match:
            pre, phone = map(int, match.groups())
            return Entity(pre+'-'+phone, 'phone')
        match = course_id_p.match(time)
        if match:
            course_id, = match.groups()
            return Entity(course_id, 'course_id')
        match = email_p.match(time)
        if match:
            email = match.groups()[0]
            return Entity(email, 'email')
        
        
        
    
    
    def parse_sent(self, sent, theta, k=10):
        sent = nltk.pos_tag(nltk.word_tokenize(sent))
        words = np.array(sent)[:, 0]
        n = len(sent)
        self.span_exps = span_exps = {}
        for i, (w, pos) in enumerate(sent):
            w = w.lower() #TODO: using it as feature?
            terms = self._lexicon.get(w, self._lexicon.get(w[:-1]))#he she it does
            span_exps[i, i] = []
            if terms is not None:
                if not terms:
                    continue
                if isinstance(terms[0], DCS):
                    for term in terms:
                        exp = term.copy((i, i))
                        span_exps[i, i].append((exp, None))
                        if isinstance(exp, Expression):
                            span_exps[i, i].extend(self.course_bridge(exp, (i, i), sent))
            else:#only if else????
                ent = self.parse_regexp(w)
                if ent is not None:
                    span_exps[i, i].append((ent.copy((i, i)), None))
                for ent_type in self._db.type2words_dict:
                    exp = LexEnt([w], ent_type, (i, i) )
                    if 0 < len(exp.execute(self._db)) < 20: 
                        span_exps[i, i].append((exp, None))
                        span_exps[i, i].extend(self.course_bridge(exp, (i, i), sent))
                
                
        for l in xrange(1, n):
            self._db.l = l
            for i in xrange(0, n - l):
                j = i + l
                span_exps[i, j] = []
                if not all(word.lower() in self._lexicon for word in words[i: j+1]):
                    for ent_type in self._db.type2words_dict:
                        exp = LexEnt(words[i: j+1], ent_type, (i, j))
                        res = exp.execute(self._db)
                        if 0 < len(res) < 20: 
                            span_exps[i, j].append((exp, None))
                            span_exps[i, j].extend(self.course_bridge(exp, (i, j), sent))
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
                                exp = None
                                dcs1, dcs2 = sorted((left, right),
                                                    key=lambda dcs: isinstance(dcs, BasePredicate) or
                                                                    (isinstance(dcs, Aggregation) and dcs.exp is None))
                                if isinstance(dcs1, Expression):
                                    if isinstance(dcs2, BasePredicate):
                                        if dcs1.type == dcs2.rtype and not (
                                                    dcs1.is_func and dcs2.is_func):
                                            exp = Join(dcs2, dcs1, (i, j), (i, m))        
                                    elif isinstance(dcs2, Expression) and not (isinstance(dcs2, Aggregation) and dcs2.exp is None):
                                        if dcs1.type == dcs2.type and not (dcs1.is_ent and dcs2.is_ent):
                                            exp = Intersect(dcs1, dcs2, (i, j))
                                    elif isinstance(dcs2, Aggregation) and dcs2.exp is None:
                                        if (dcs2.rtype is None or dcs2.rtype == dcs1.type):
                                            exp = dcs2.copy((i, j), dcs1)
                                            # if exp is not None:
                                    if exp is not None:
                                        exps.append((exp, self._feature_extractor.extract_features(sent, exp)))
                                        exps.extend(self.course_bridge(exp, (i, j), sent))
                                            
                                            
                #bridge
                #exps.extend([join for exp, _ in exps if isinstance(exp, Expression) for join in self.bridge(sent, exp)])
                exps.sort(reverse=True, key=lambda (exp, feats): feats.dot(theta) if feats is not None else -np.inf)
                span_exps[i, j] = exps[:k]
        return sorted(((exp, feats) for exps in span_exps.values() for (exp, feats) in exps if feats is not None), key=lambda (exp, feats): feats.dot(theta), reverse=True)[:k]
