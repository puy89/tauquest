import numpy as np
import nltk
from db import Join, Intersect, Courses, Lecturers, Count, Max, Min
N = 2000
MAX_JOIN = 10
MAX_INTERSECT = 10
all_poss = np.array(['WP', 'VBZ', 'DT', 'JJ', 'NN', 'IN', 'DT', 'NN', 'IN', 'NNP', '.'])
NUM_POS = len(all_poss)
SHORT_LENS = np.arange(3)

def extract_features(sent, exp):
    feats = np.zeros(N)
    i = 0
	counts = [0, 0]
	joins = []
	intersections = []
    def dfs(node):
		if type(node) is Join:
			joins.append((node.pred_span, node.un.span))
			dfs(node.un)
		if type(node) is Intersect:
			intersections.append((node.pred_span, node.span))
			dfs(node.exp1)
			dfs(node.exp2)
    dfs(exp)
	ldcs =  str(exp)
    feats[i] =  len(joins); i += 1
    feats[i] =  len(intersections); i += 1
    ents =  exp.execute()
    feats[i: i+len(SHORT_LENS)] =  SHORT_LENS == len(ents); i += len(SHORT_LENS)
    feats[i] = len(ents) >= 3; i += 1
	for join in joins:
	    for token in join:
	        feats[i: i + NUM_POS] = all_poss == sents[token[0]][1]; i += NUM_POS
	i += (MAX_JOIN - len(join))*NUM_POS
	for intersect in intersects:
	    for token in intersect:
	        feats[i: i + NUM_POS] = all_poss == sents[token[0]][1]; i += NUM_POS
	i += (MAX_JOIN - len(join))*NUM_POS
    return feats

lexicon = {'who': ['lecturer'],
           'teach': ['lecturer'],
           'when': ['day', 'start_time', 'semester'], # add full time
           'email': ['email'],
           'address': ['email'],
           'phone': ['phone', 'rev_phone'],
           'number': ['phone', 'fax', 'room', 'id'],
           'where': ['room', 'building', 'office'],
           'room': ['room'],#change place to room, add full adress
           'semester': ['semester'],
           'kind': ['kind'],
           'end': ['end_time'],
           'start': ['start_time'],
           'much': : ['count'],
           'after': ['<', '<='],
           'before': ['>', '>='],
          }

def update_lexicon(db):
    for opts in in lexicon.values():
        for opt in list(opts):
            if hasattr(Course, opt) or hasattr(Lecturer, opt):
                opts.append('rev_'+opt)
    for course in db.courses.values():
        lexicon[course.name] = course
        lexicon[course.name.lower()] = course
    #TODO: add english name of lecturers


    
def parse_sent(sent, theta, k=10):
    sent = nltk.pos_tag(nltk.word_tokenize(sent))
    n = len(sents)
    span_exps = {(i, i): lexicon.get(w) for i, (w, pos) in enumerate(sent)}
    for l in xrange(1, n):
        for i in xrange(0, n-l):
            j = i+l
            exps = span_exps[i, j] = [None]
            for l in xrange(i, j+1):
                left = span_exps[i, l]
                right = span_exps[l, j]
                if type(left) is str:
                    if isinstance(rev,  Expression):
                        exps.append(Join())