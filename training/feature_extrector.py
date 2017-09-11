import numpy as np
from expression.expression import Join, Intersect, LexEnt
from nltk.data import load

NUMBER_OF_FEATURES = 3000

tagdict = load('help/tagsets/upenn_tagset.pickle')

# TO DO: make sure this is all POS
all_poss = np.array(tagdict.keys())
pos2idx = {pos: i for i, pos in enumerate(all_poss)}
pair_pos2idx = {pair_pos: i for i, pair_pos in enumerate([(pos1, pos2) for pos1 in all_poss for pos2 in all_poss])}

NUM_POS = len(all_poss)
SHORT_LENS = np.arange(3)


class FeatureExtractor:
    def __init__(self, db):
        self._db = db

    def extract_features(self, sent, exp):
        feats = np.zeros(NUMBER_OF_FEATURES)
        i = 0
        counts = [0, 0]
        joins = []
        n_intersects = [0]
        bridges = []
        skips = []
        lex_ents_feats = [0]
        def dfs(node):
            if type(node) is Join:
                if node.is_bridge:
                    bridges.append((node.pred.span[0], node.un.span[0]))
                else:
                    joins.append((node.pred.span[0], node.un.span[0]))
                left_bound = min(node.pred.span[0], node.un.span[0]) + 1
                right_bound = max(node.pred.span[0], node.un.span[0])
                if right_bound > left_bound:
                    skips.append((left_bound, right_bound))
                dfs(node.un)
            if type(node) is Intersect:
                n_intersects[0] += 1
                left_bound = min(node.exp1.span[0], node.exp2.span[0]) + 1
                right_bound = max(node.exp1.span[0], node.exp2.span[0])
                if right_bound > left_bound:
                    skips.append((left_bound, right_bound))
                dfs(node.exp1)
                dfs(node.exp2)
                # TODO bridge
            if type(node) is LexEnt:
                assert node.pwords is not None
                feats[i:i+2] += node.pcapital, node.pwords
        if exp.span[0] > 0:
            skips.append((0, exp.span[0]))
        if exp.span[1] < len(sent)-1:
            skips.append((exp.span[1], len(sent)))
        #lexicon features
        dfs(exp)
        i += 2
        # Rule features
        feats[i] = len(joins);
        i += 1
        feats[i] = len(bridges);
        i += 1
        feats[i] = n_intersects[0]
        i += 1
        # skip POS
        for left_bound, right_bound in skips:
            for j in xrange(left_bound, right_bound):
                feats[i + pos2idx[sent[j][1]]] = 1
        i += NUM_POS
        # composition POS
        for join in joins:
            idx = pair_pos2idx[sent[join[0]][1], sent[join[1]][1]]
            feats[i + idx] = 1
        for intersect in bridges:
            idx = pair_pos2idx[sent[intersect[0]][1], sent[intersect[1]][1]]
            feats[i + idx] = 1
        i += len(all_poss) ** 2
        # Denotation features
        if exp.is_func:
            # stupid trick
            len_ents = 0.5
        else:
            len_ents = len(exp.execute(self._db))
        feats[i: i + len(SHORT_LENS)] = SHORT_LENS == len_ents;
        i += len(SHORT_LENS)
        feats[i] = len_ents >= 3;
        i += 1

        return feats
