#!/usr/bin/env python
import argparse
import os
import subprocess
import re
import pickle

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from conllxdataset import ConllXDataset
from conlludataset import ConllUDataset
from features import get_features
from model import Perceptron
from evaluate import evaluate


def get_data(args):
    if args.ud:
        dataset = ConllUDataset
    else:
        dataset = ConllXDataset
    data_dir = os.path.expanduser(args.data)
    # TODO: remove name dependency.
    train_dataset = dataset(os.path.join(data_dir, 'train.conll'))
    dev_dataset = dataset(os.path.join(data_dir, 'dev.conll'))
    test_dataset = dataset(os.path.join(data_dir, 'test.conll'))
    return train_dataset, dev_dataset, test_dataset


def plot(args):
    print(f'Loading data from `{args.data}`...')
    _, dev_dataset, _ = get_data(args)
    print(f'Loading model from `{args.model}`...')
    with open(args.model, 'rb') as f:
        model = pickle.load(f)
    n = 5
    print(f'Saving plots of {n} score matrices at `image/`...')
    for i, tokens in enumerate(dev_dataset.tokens[:n]):
        tree, probs =  model.parse(tokens)
        plt.imshow(probs)
        plt.savefig(f'image/pred{i}.pdf')


def train(args):
    print(f'Loading dataset from `{args.data}`...')
    train_dataset, dev_dataset, test_dataset = get_data(args)
    train_tokens = train_dataset.tokens[:args.max_lines]
    dev_tokens = dev_dataset.tokens
    test_tokens = dev_dataset.tokens

    for dir in ('models', 'out'):
        if not os.path.exists(dir):
            os.makedirs(dir)

    # Obtain the feature-set.
    if args.features is not None:
        # Making features can take a long time, so we optionally pickle and load them.
        print(f'Loading feature-set from `{args.features}`...')
        with open(args.features, 'rb') as f:
            features = pickle.load(f)
    else:
        # Otherwise, get feature-set from the training sentences.
        print('Creating feature-set...')
        features = set()
        for tokens in tqdm(train_tokens):
            # We want the features of _all_ possible head-dep combinations
            # in order to produce full score matrices at prediction time.
            for head in tokens:
                for dep in tokens:
                    features.update(get_features(head, dep, tokens))

        dump_path = 'models/features.pkl'
        print(f'Saving features at `{dump_path}`...')
        with open(dump_path, 'wb') as f:
            # TODO: dump to a specific folder, maybe timestamped,
            # not to overwrite older feature-sets.
            pickle.dump(features, f)
    print(f'Number of features: {len(features):,}.')

    # Initialize model.
    model = Perceptron(features)
    # Train model.
    try:
        model.train(args.epochs, train_tokens, dev_set=dev_tokens)
    except KeyboardInterrupt:
        print('Exiting training early.')

    # Evaluate model.
    print('Evaluating on dev set...')
    dev_acc = model.evaluate(dev_tokens)
    print(f'Dev UAS {dev_acc:.2f} |')
    print('Top features:')
    top_features = model.top_features(30)
    print('\n'.join(f'{f} {v:.4f}' for f, v in top_features))
    print()

    model.average_weights()

    # Evaluate again (to see difference).
    print('Evaluating on dev set...')
    dev_acc = model.evaluate(dev_tokens)
    print(f'Dev UAS {dev_acc:.2f} |')
    print('Top features:')
    top_features = model.top_features(30)
    print('\n'.join(f'{f} {v:.4f}' for f, v in top_features))
    print()

    model.prune()

    print(f'Saving model to `{args.model}`...')
    model.save(args.model)

    print('Finished.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['train', 'eval', 'plot'])
    parser.add_argument('--data', type=str, default='~/data/stanford-ptb')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--model', type=str, default='models/model.pkl')
    parser.add_argument('--features', default=None)
    parser.add_argument('--out', type=str, default='out')
    parser.add_argument('-n', '--max-lines', type=int, default=-1)
    parser.add_argument('--ud', action='store_true')
    args = parser.parse_args()

    if args.mode == 'train':
        train(args)
    if args.mode == 'eval':
        evaluate(args)
    if args.mode == 'plot':
        plot(args)
