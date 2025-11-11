# A rather trivial script that reports how many instances of each AUX tagged lemma occurs in the dataset

from collections import Counter
import glob
import os

from stanza.utils.conll import CoNLL

aux_lemmas = Counter()
filenames = glob.glob("../xpos_features/*")
for filename in filenames:
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            if word.upos == 'AUX' and word.lemma:
                aux_lemmas[word.lemma] += 1

for lemma in sorted(aux_lemmas):
    print(lemma, aux_lemmas[lemma])

