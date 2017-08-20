import numpy as np
import nltk
from db import (Expression, Entity, Join, Intersect, Courses, Lecturers, Count, Max, Min,
               Course, Lecturer, Predicate)
N = 2000
MAX_JOIN = 10
MAX_INTERSECT = 10
all_poss = np.array(['WP', 'VBZ', 'DT', 'JJ', 'NN', 'IN', 'DT', 'NN', 'IN', 'NNP', '.'])
NUM_POS = len(all_poss)
SHORT_LENS = np.arange(3)

def extract_features(sent, exp, db):
    feats = np.zeros(N)
    i = 0
    counts = [0, 0]
    joins = []
    intersects = []
    def dfs(node):
        if type(node) is Join:
            joins.append((node.pred.span, node.un.span))
            dfs(node.un)
        if type(node) is Intersect:
            intersects.append((node.exp1.span, node.exp1.span))
            dfs(node.exp1)
            dfs(node.exp2)
        #TODO bridge
    dfs(exp)
    ldcs =  str(exp)
    feats[i] =  len(joins); i += 1
    feats[i] =  len(intersects); i += 1
    #TODO bridge
    if exp.is_func:
        #stupid trick
        len_ents = 0.5
    else:
        len_ents =  len(exp.execute(db))
    feats[i: i+len(SHORT_LENS)] =  SHORT_LENS == len_ents; i += len(SHORT_LENS)
    feats[i] = len_ents >= 3; i += 1
    for join in joins:
        for token in join:
            feats[i: i + NUM_POS] = all_poss == sent[token[0]][1]; i += NUM_POS
    i += (MAX_JOIN - len(joins))*NUM_POS
    for intersect in intersects:
        for token in intersect:
            feats[i: i + NUM_POS] = all_poss == sent[token[0]][1]; i += NUM_POS
    i += (MAX_JOIN - len(intersects))*NUM_POS
    return feats

lexicon = {'who': ['lecturer'],
           'teach': ['lecturer'],
           'when': ['day', 'start_time', 'semester'], # add full time
           'email': ['email'],
           'address': ['email'],
           'phone': ['phone'],
           'number': ['phone', 'fax', 'place', 'id'],
           'where': ['place', 'building', 'office'],
           'place': ['place'],#TODO: change place to room, add full adress
           'semester': ['semester'],
           'kind': ['kind'],
           'end': ['end_time'],
           'start': ['start_time'],
           'much': ['count'],
           'after': ['>', '>='],
           'before': ['<', '<='],
          }

def update_lexicon(db):
    for k, opts in lexicon.items():
        parsed_opts = []
        for opt in opts:
            parsed_opts.append(Predicate(opt))
            if parsed_opts[-1].is_attr:
                parsed_opts.append(Predicate('rev_'+opt))
        lexicon[k] = parsed_opts
    for course in db.courses.values():
        lexicon.setdefault(course.name,  []).append(Entity(course.id, Course))
        lexicon.setdefault(course.name.lower(),  []).append(Entity(course.id, Course))
    #TODO: add english name of lecturers

    
def parse_sent(sent, theta, db, k=10):
    #slowwwwwwwwww!!!!!
    for course in db.courses.values():
        if course.name in sent:
            sent = sent.replace(course.name, course.name.replace(' ', '-'))
    sent = nltk.pos_tag(nltk.word_tokenize(sent))
    n = len(sent)
    span_exps = {}
    for i, (w, pos) in enumerate(sent):
        terms = lexicon.get(w.replace('-', ' '))
        span_exps[i, i] = []
        if terms is not None:
            if isinstance(terms[0],  Expression):
                for term in terms:
                    term.span = i, i
            if isinstance(terms[0],  Predicate):
                for term in terms:
                    term.span = i, i       
            span_exps[i, i].extend(terms)
    for l in xrange(1, n):
        for i in xrange(0, n-l):
            j = i+l
            exps = []                
            for m in xrange(i, j):
                if len(span_exps[m+1, j]) == 0:
                    for left in span_exps[i, m]:
                        exps.append(left)
                elif len(span_exps[i, m]) == 0:
                    for right in span_exps[m+1, j]:
                        exps.append(right)
                else:
                    for left in span_exps[i, m]:                         
                        for right in span_exps[m+1, j]:
                            if  isinstance(left,  Predicate):
                                if isinstance(right,  Expression) and right.type == left.rtype:                                    
                                    exps.append(Join(left, right, (i, j), (i, m)))
                            elif isinstance(left,  Expression):
                                if isinstance(right,  Predicate) and left.type == right.rtype:
                                    exps.append(Join(right, left, (i, j), (m+1, j)))
                                elif isinstance(right,  Expression):
                                    if right.type == left.type:
                                        exps.append(Intersect(right, left, (i, j)))
            #TODO create predicate Class??
            exps.sort(key=lambda exp: extract_features(sent, exp, db).dot(theta) if isinstance(exp,  Expression) else 0)
            span_exps[i, j] = exps[:k]
    1/0
    return span_exps[0, n-1][0]