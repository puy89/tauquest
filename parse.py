import csv

import numpy as np
from datetime import datetime
import nltk

from db.db import (Expression, Entity, Join, Intersect, Courses, Lecturers, Count, Max, Min,
               Course, Lecturer, Predicate, Aggregation, aggregats)

N = 2000
MAX_JOIN = 10
MAX_INTERSECT = 10
#TO DO: make sure this is all POS
all_poss = np.array(['WP', 'VBZ', 'DT', 'JJ', 'NN', 'IN', 'DT', 'NNS', 'IN', 'NNP', 'CD', '.'])
pos2idx = {pos: i  for i, pos in enumerate(all_poss)}
pair_pos2idx = {pair_pos: i  for i, pair_pos in enumerate([(pos1, pos2) for pos1 in all_poss for pos2 in all_poss])}

NUM_POS = len(all_poss)
SHORT_LENS = np.arange(3)

def extract_features(sent, exp, db):
    feats = np.zeros(N)
    i = 0
    counts = [0, 0]
    joins = []
    intersects = []
    skips = []
    def dfs(node):
        if type(node) is Join:
            joins.append((node.pred.span[0], node.un.span[0]))
            left_bound = min(node.pred.span[0], node.un.span[0]) + 1
            right_bound = max(node.pred.span[0], node.un.span[0])
            if right_bound > left_bound:
                skips.append((left_bound, right_bound))
            dfs(node.un)
        if type(node) is Intersect:
            intersects.append((node.exp1.span[0], node.exp2.span[0]))
            left_bound = min(node.exp1.span[0], node.exp2.span[0]) + 1
            right_bound = max(node.exp1.span[0], node.exp2.span[0])
            if right_bound > left_bound:
                skips.append((left_bound, right_bound))
            dfs(node.exp1)
            dfs(node.exp2)
        #TODO bridge
    dfs(exp)
    ldcs =  str(exp)
    #Rule features
    #TODO bridge
    feats[i] =  len(joins); i += 1
    feats[i] =  len(intersects); i += 1
    #skip POS
    for left_bound, right_bound in skips:
        for j in xrange(left_bound, right_bound):
            feats[i + pos2idx[sent[j][1]]] = 1
    i += NUM_POS
    #composition POS    
    for join in joins:
        idx = pair_pos2idx[sent[join[0]][1], sent[join[1]][1]]
        feats[i + idx] = 1
    for intersect in intersects:
        idx = pair_pos2idx[sent[intersect[0]][1], sent[intersect[1]][1]]
        feats[i + idx] = 1
    i += len(all_poss) ** 2
    #Denotation features
    if exp.is_func:
        #stupid trick
        len_ents = 0.5
    else:
        len_ents =  len(exp.execute(db))
    feats[i: i+len(SHORT_LENS)] =  SHORT_LENS == len_ents; i += len(SHORT_LENS)
    feats[i] = len_ents >= 3; i += 1

    return feats

lexicon = {'who': ['lecturer'],
           'teach': ['lecturer', 'teach'],
           'taught': ['lecturer', 'teach'],
           'lecturer': ['lecturer', 'teach'],
           'when': ['day', 'start_time', 'semester'], # add full time
           'email': ['email'],
           'address': ['email'],
           'phone': ['phone'],
           'number': ['phone', 'fax', 'place', 'id'],
		   'room': ['place'],
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
            aggregat_cls = aggregats.get(opt)
            if aggregat_cls is not None:
                parsed_opts.append(aggregat_cls())
            else:
                parsed_opts.append(Predicate(opt))
                if parsed_opts[-1].is_attr:
                    parsed_opts.append(Predicate('rev_'+opt))
        lexicon[k] = parsed_opts
    for course in db.courses.values():
        lexicon.setdefault(course.name,  []).append(Entity(course.id, Course))
        lexicon.setdefault(course.name.lower(),  []).append(Entity(course.id, Course))
    for lecturer in db.lecturers.values():
        if lecturer.name: #not created when created courses table
            lexicon.setdefault(lecturer.name,  []).append(Entity(lecturer.id, Lecturer))
            lexicon.setdefault(lecturer.name.lower(),  []).append(Entity(lecturer.id, Lecturer))
    
        
    #TODO: add english name of lecturers

    
def parse_sent(sent, theta, db, k=10):
    #slowwwwwwwwww!!!!!
    for course in db.courses.values():
        if course.name in sent:
            sent = sent.replace(course.name, course.name.replace(' ', '-'))
    for lecturer in db.lecturers.values():
        if lecturer.name: #not created when created courses table
            if lecturer.name in sent:
                sent = sent.replace(lecturer.name, lecturer.name.replace(' ', '-'))
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
                    span_exps[i, i].append((term, None))
            elif isinstance(terms[0],  Predicate):
                for term in terms:
                    term.span = i, i
                    span_exps[i, i].append((term, None))
            elif isinstance(terms[0],  Aggregation):
                for term in terms:
                    term.span = i, i
                    span_exps[i, i].append((term, None))
    for l in xrange(1, n):
        for i in xrange(0, n-l):
            j = i+l
            exps = []                
            for m in xrange(i, j):
                for h in xrange(m+1, j+1):
                    if not (len(span_exps[i, m]) and len(span_exps[h, j])):
                        continue
                    for left, _ in span_exps[i, m]:                         
                        for right, _ in span_exps[h, j]:
                            if  isinstance(left,  Predicate):
                                if isinstance(right,  Expression) and right.type == left.rtype and not (left.is_func and right.is_func):
                                    exp = Join(left, right, (i, j), (i, m))
                                    exps.append((exp, extract_features(sent, exp, db)))
                            elif isinstance(left,  Expression):
                                if isinstance(right,  Predicate) and left.type == right.rtype and not (left.is_func and right.is_func):
                                    exp = Join(right, left, (i, j), (m+1, j))
                                    exps.append((exp, extract_features(sent, exp, db)))
                                elif isinstance(right,  Expression):
                                    if right.type == left.type:
                                        exp = Intersect(right, left, (i, j))
                                        exps.append((exp, extract_features(sent, exp, db)))
                                elif isinstance(right,  Aggregation):
                                    exp = type(right)(left)
                                    exps.append((exp, extract_features(sent, exp, db)))
                            elif isinstance(left,  Aggregation):
                                if isinstance(right,  Expression): 
                                    exp = type(left)(right)
                                    exps.append((exp, extract_features(sent, exp, db)))
                #if exp is not None:
                    
                                    
            exps.sort(key=lambda (exp, feats): feats.dot(theta) if feats is not None else np.inf)
            span_exps[i, j] = exps[-k:]
    return span_exps[0, n-1]

eps = 1e-06

def adagrad(gradient, x0, step, iterations, PRINT_EVERY=10):
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
        x -= step*grad/(np.sqrt(G)+eps)
        ### END YOUR CODE


        if iter % ANNEAL_EVERY == 0:
            step *= 0.5

    return x

    
def train(quests, ans, db, k=10, iters=None):
    def gradient(theta):
        i = np.random.randint(0, len(quests))
        exps, feats = np.array(parse_sent(quests[i], theta, db, k)).T
        feats = np.array([feat for feat in feats], float)
        ps = np.exp(feats.dot(theta))
        agree = [exp.execute(db) == ans[i] for exp in exps]
        assert any(agree)
        unnormed = ps*agree
        qs = unnormed/unnormed.sum()
        return feats.T.dot(qs - ps)
    iters = iters or len(quests)
    return adagrad(gradient, np.zeros(N), 0.01, iters)

def load_dataset(fn='questions-answers.csv'):
    f = open(fn)
    r = csv.reader(f)
    quests, ans = np.array([(row[0], set(row[1:])) for row in r]).T
    f.close()
    return quests, ans