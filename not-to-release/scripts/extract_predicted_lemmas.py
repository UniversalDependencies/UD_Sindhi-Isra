"""
This script gathers words from a Stanza lemmatizer's prediction output

It drops all words already in the ../lemmas/* directory
Outputs in .tsv format
"""

import glob
import sys
from operator import itemgetter

from stanza.utils.conll import CoNLL

def read_known_lemmas():
    lemmas = set()
    known_lemma_files = sorted(glob.glob("../lemmas/*.tsv"))
    for lemma_file in known_lemma_files:
        with open(lemma_file) as fin:
            tsv = fin.readlines()
            tsv = [x.strip() for x in tsv[1:]]
            tsv = [x for x in tsv if x]
        for line in tsv:
            pieces = line.split("\t")
            assert len(pieces) >= 3
            lemmas.add((pieces[0], pieces[1]))
    return lemmas

known_lemmas = read_known_lemmas()

pred_filename = "sd_isra.test.pred.conllu"
pred_doc = CoNLL.conll2doc(pred_filename)

orig_filename = "sd_isra.test.in.conllu"
orig_doc = CoNLL.conll2doc(orig_filename)

assert len(pred_doc.sentences) == len(orig_doc.sentences)

lemmas = {}
skipped = 0

for pred_sent, orig_sent in zip(pred_doc.sentences, orig_doc.sentences):
    assert len(pred_sent.words) == len(orig_sent.words)
    for pred_word, orig_word in zip(pred_sent.words, orig_sent.words):
        if not orig_word.lemma:
            if (orig_word.text, orig_word.upos) in known_lemmas:
                skipped += 1
                continue
            lemmas[(pred_word.text, pred_word.upos)] = pred_word.lemma
    if len(lemmas) > 1000:
        break

print("Skipped %d words" % skipped, file=sys.stderr)

keys = sorted(lemmas, key=itemgetter(1, 0))
for k in keys:
    print("%s\t%s\t%s" % (k[0], k[1], lemmas[k]))
