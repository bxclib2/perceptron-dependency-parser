# Perceptron dependency parser
A graph-based dependency parser, trained on linguistic features with the (averaged) structured-perceptron.
This project is an mash-up of the following ingredients:

### Graph based dependency parsing
Dependecy parsing with an MST algorithm from [McDonald et al. 2006](https://www.seas.upenn.edu/~strctlrn/bib/PDF/nonprojectiveHLT-EMNLP2005.pdf), and the training objective of [Dozat and Manning 2017](https://arxiv.org/pdf/1611.01734.pdf) (for each token predict a head).

### Structured perceptron algorithm
Inspired by and partially based on the spaCy blog posts [Parsing English in 500 Lines of Python](https://explosion.ai/blog/parsing-english-in-python) and [A Good Part-of-Speech Tagger in about 200 Lines of Python](https://explosion.ai/blog/part-of-speech-pos-tagger-in-python).

### Linguistic features
The feature-set is largely taken from [McDonald et al. 2005](https://www.seas.upenn.edu/~strctlrn/bib/PDF/dependencyACL2005.pdf). For the Universal Dependencies dataset we can also make good use of the `lemma` and `feats` fields, but I haven't come around to this yet.

### Data handling
All code to do handle `conllu` and `conllx` files is taken from [bastings](https://github.com/bastings/parser/tree/extended_parser) parser.

## Usage
For now we assume you have the PTB in train/dev/test splits in conll-format, stored somewhere in one directory, and that they are named `train.conll`, `dev.conll`, `test.conll`. For later we will to include a data script that downloads some of the Universal Dependencies languages, so we don't have this manual step.

To train the perceptron for 5 epochs, type:
```
./main.py train --data path/to/ptb/dir --epochs 5
```
The training can be halted at any point with `cntrl-c`. The trained model and feature-set are saved at `models/model.pkl` resp. `models/features.pkl` by default. To specify these paths use `--model` resp. `--features`.

To train the perceptron for 5 epochs with already extracted features, type:
```
./main.py train --data path/to/ptb/dir --epochs 5 --features path/to/features
```

To evaluate the trained perceptron, type:
```
./main.py eval --data path/to/ptb/dir
```

To plot heatmaps of the predicted score matrices for five sentences in the dev set (like those in [image](image)) type:
```
./main.py plot --data path/to/ptb/dir
```

## Features
The basic features are all of the following form:
```
head dep pos pos=VBN VBZ
head dep word word=is a
head dep pos word=VBN have
head dep suffix suffix=ing is
head dep shape shape=Xxxx dd/dd/ddd
head dep shape shape=xxxx xx
```
With shape inspired by spaCy's `token.shape` feature. This feature-set has no positional, context or otherwise sentence-level features.

Optionally you can add distance:
```
head dep pos pos=VBN have (-1)
head dep word word=is a (1)
```
With `(-1)` indicating the linear distance from the head to the dependent. This is a cheap way of giving some sentence-level information to the model.

Optionally you can add left and right surrounding pos tags for context:
```
head dep i i+1/i-1 i=DT NNS/VBZ VBG
```
with `i i+1` meaning the word itself and its right neighbor.

Finally there is an 'in-between' feature that finds all tags linearly in between head and dependent:
```
head between dep=DT JJ NNS (2 1)
```
With `(2 1)` indicating respectively the distance from head to between, and from between to dependent.

To choose these additional features for the model, type:
```
./main.py train --features dist surround between
```
(Or any combination from these three.)

## Speed and size
Making the full feature set for the training set (~66 million for the basic features) takes about 14 minutes. One epoch with these features on the training set also takes around 15 minutes (~40 sentences per second). After training, we prune the model by removing weights smaller than a certain threshold (1e-3 by default):
```
Pruning weights with threshold 0.001...
Number of weights: 66,475,707 (64,130,339 exactly zero).
Number of pruned weights: 2,343,424.
```
Due to the sheer enormity of the feature-set, the model saved model is still pretty big: ~140 MB!

## Accuracy
A fully converged training run (15 epochs) on the minimal feature-set gave the following results:
```
Train UAS 96.43
Dev UAS 81.98
Test UAS 81.58
```
Averaging the weights makes quite a difference on the dev-set: from 78.48 to 81.98.

## Interpretation
Fun fact one: the trained weights of the features are extremely interpretable. Here are the largest ones (from the simple feature-set):
```
distance=1 29.9918
distance=-1 27.3818
distance=-2 22.3953
distance=2 21.1036
distance=3 18.2438
head dep pos pos=NN PRP$ 17.6982
head dep pos pos=NNS PRP$ 16.0800
head dep pos word=NN a 15.4661
head dep pos pos=NN DT 15.3968
distance=-3 15.1488
head dep shape shape=XXXXX . 14.9128
head dep pos word=NN of 14.8744
head pos=VBN 14.7640
head dep pos word=VBZ . 14.7317
head dep pos pos=VBD . 14.5186
head dep pos pos=NNS JJ 14.3879
head pos=VBD 14.3672
head pos=VBZ 14.0784
head dep pos pos=VBZ . 14.0720
distance=4 13.8039
head dep pos pos=NN JJ 13.1833
head dep pos pos=IN NNS 12.8427
head dep pos word=CD than 12.7341
head pos=VBP 12.6299
head dep word pos=% CD 12.5798
head dep pos pos=NNS DT 12.5320
head dep pos word=VBP . 12.3965
head dep pos word=VB that 12.3921
head dep pos pos=IN NNPS 12.3371
head dep pos word=VBD . 12.2725
```
Fun fact two: We can make some nifty [heatmaps](image) out of the score matrices.

## Requirements
```
python>=3.6.0
numpy
matplotlib
tqdm
```

## TODO
- [ ] Predict labels. Maybe a second perceptron altogether for that?
- [ ] Make integration with Universal Dependencies easier. (Now only using conllx format)
- [ ] Make data loading less name-dependent.
- [ ] Understand which features matter.
- [X] Perform full training till convergence.
- [ ] Make training parallel ('hogwild'). Really easy, and perhaps even some regularization.
- [X] Prune the averaged weights by removing all features that are exactly 0.
