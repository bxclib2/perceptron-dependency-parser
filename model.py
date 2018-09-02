import pickle

import numpy as np
from tqdm import tqdm

from features import shape, get_features
from mst import get_best_graph, softmax


class Perceptron:
    def __init__(self, feature_set, complex_features=False):
        self.weights = dict((f, 0) for f in feature_set)
        self._totals = dict((f, 0) for f in feature_set)
        self._timestamps = dict((f, 0) for f in feature_set)
        self.complex_features = complex_features
        self.i = 0

    def score(self, features):
        all_weights = self.weights
        score = 0.0
        for f in features:
            if f not in all_weights:
                continue
            score += all_weights[f]
        return score

    def predict(self, token, tokens):
        scores = []
        features = []
        for head in tokens:
            feats = get_features(head, token, tokens, self.complex_features)
            score = self.score(feats)
            features.append(feats)
            scores.append(score)
        guess = np.argmax(scores)
        return guess, features

    def update(self, guess_features, true_features):
        def upd_feat(f, v):
            if f not in self.weights:
                pass
            else:
                nr_iters_at_this_weight = self.i - self._timestamps[f]  # For the times we skipped this feature.
                self._totals[f] += nr_iters_at_this_weight * self.weights[f]
                self.weights[f] += v
                self._timestamps[f] = self.i

        self.i += 1
        for f in true_features:
            upd_feat(f, 1.0)
        for f in guess_features:
            upd_feat(f, -1.0)

    def train(self, niters, lines):
        for i in range(1, niters+1):
            c = 0; n = 0
            for j, line in enumerate(tqdm(lines)):
                # print(f'Line {j}/{len(lines)}', end='\r')
                for token in line:
                    guess, features = self.predict(token, line)
                    self.update(features[guess], features[token.head])
                    c += guess == token.head; n += 1
            acc = self.evaluate(lines[:20])
            print(f'| Iter {i} | Correct guess {c:,}/{n:,} | Train UAS {acc:.2f} |')
            # TODO: print(f'| Iter {i} | Correct guess {c:,}/{n:,} | Train UAS {acc:.2f} | Dev UAS {dev_acc:.2f}')
            np.random.shuffle(lines)

    def average_weights(self):
        print('Averaging model weights...')
        self.weights = dict((f, val/self.i) for f, val in self._totals.items())
        del self._totals, self._timestamps

    def test(self, line):
        pred, _ = self.parse(line)
        gold = [token.head for token in line]
        return self.accuracy(pred, gold)

    def accuracy(self, pred, gold):
        return 100 * sum((p == g for p, g in zip(pred, gold))) / len(pred)

    def evaluate(self, lines):
        acc = 0.0
        for line in lines:
            acc += self.test(line)
        return acc / len(lines)

    def parse(self, tokens):
        score_matrix = np.zeros((len(tokens), len(tokens)))
        for i, dep in enumerate(tokens):
            for j, head in enumerate(tokens):
                features = get_features(head, dep, tokens, self.complex_features)
                score = self.score(features)
                score_matrix[i][j] = score
        probs = softmax(score_matrix)
        tree = get_best_graph(probs)
        return tree, probs

    def save(self, path):
        path = path + '.pkl' if not path.endswith('.pkl') else path
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def top_features(self, n):
        top_weights = sorted(self.weights.items(), reverse=True, key=lambda x: x[1])
        return top_weights[:n]
