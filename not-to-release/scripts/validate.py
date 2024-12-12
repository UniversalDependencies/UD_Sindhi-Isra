import argparse
import re
import sys

import networkx as nx

from stanza.utils.conll import CoNLL

ALLOWED_UPOS = { "ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB"}

ALLOWED_UPOS_TO_XPOS = {
    "NOUN":  ["NN", "NNX"],
    "PROPN": ["NNP"],
    "ADJ":   ["JJ", "JJC", "JJO", "JJM", "JJF"],
    "PRON":  ["PRP", "PRD", "PRWH", "PRL"],
    "ADV":   ["ADV", "ADT", "ADM", "ADN", "ADQ", "ADA", "ADS", "ADP", "ADPX"],
    "ADP":   ["PSP", "PSPX"],
    "CCONJ": ["CC"],
    "SCONJ": ["CS"],
    "AUX":   ["VAUX", "VAUXX", "VAUXN"],
    "VERB":  ["VM", "VMX"],
    "PUNCT": ["PUNCT"],
    "PART":  ["PART"],
    "NUM":   ["NUM"],
    "DET":   ["PRD"],
    "INTJ":  ["INTJ"],
}

ALLOWED_UPOS_TO_FEATS = {
    "ADJ":   ['Case=Acc', 'Case=Nom', 'Degree=Cmp', 'Degree=Pos', 'Degree=Sup', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing'],
    "ADP":   ['Case=Acc', 'Case=Gen', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3', 'Type=Gen', 'Type=Loc'],
    "ADV":   ['Case=Acc', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3'],
    "AUX":   ['AuxType=Be', 'Gender=Fem', 'Gender=Masc', 'Mood=Sub', 'Number=Plur', 'Number=Sing', 'Person=1', 'Person=2', 'Person=3', 'Tense=Fut', 'Tense=Past', 'Tense=Pres'],
    "CCONJ": [],
    "DET":   ['Case=Acc', 'Case=Gen', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3'],
    "INTJ":  [],
    "NOUN":  ['Case=Abl', 'Case=Acc', 'Case=Nom', 'Case=Voc', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3'],
    "NUM":   ['Case=Nom', 'Number=Sing'],
    "PART":  ['PartType=Emp'],
    "PRON":  ['Case=Acc', 'Case=Gen', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=1', 'Person=2', 'Person=3'],
    "PROPN": ['Case=Abl', 'Case=Acc', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Sing'],
    "PUNCT": [],
    "SCONJ": [],
    "SYM":   [],
    "VERB":  ['Aspect=Con', 'Aspect=Imp', 'Aspect=Perf',
              'Case=Acc', 'Case=Nom',
              'Gender=Fem', 'Gender=Masc', 'Gender[Obj]=Masc', 'Gender[Subj]=Fem', 'Gender[Subj]=Masc',
              'Mood=Des',
              'Number=Plur', 'Number=Sing', 'Number[Obj]=Plur', 'Number[Obj]=Sing', 'Number[Subj]=Plur', 'Number[Subj]=Sing',
              'Person=1', 'Person=2', 'Person=3', 'Person[Obj]=1', 'Person[Obj]=2', 'Person[Obj]=3', 'Person[Subj]=1', 'Person[Subj]=2', 'Person[Subj]=3',
              'Tense=Fut', 'Tense=Past', 'Tense=Pres',
              'VerbForm=Caus', 'VerbForm=ConjPart', 'VerbForm=FutPart', 'VerbForm=Inf', 'VerbForm=PastPart', 'VerbForm=PresPart', 'VerbForm=VerbNoun',
              'Voice=Act', 'Voice=Pass'],
}

DISALLOWED_BLANK_FEATS = {"NOUN", "PROPN"}

ALLOWED_PUNCT_CHARS = r"؟–؛!\"().,-/:،“”"
ALLOWED_PUNCT_WORD = re.compile("[%s]+" % ALLOWED_PUNCT_CHARS)

def validate(new_doc, print_sent_idx=False, check_xpos=True, check_feats=True):
    problem_sentences = set()

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.upos not in ALLOWED_UPOS:
                if not printed:
                    print("UNKNOWN UPOS")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d had an unknown upos |%s|" % (sent.sent_id, sent_idx, word_idx, word.upos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        if not any(word.deprel == 'root' for word in sent.words):
            if not printed:
                print("NO ROOT SENTENCES")
                printed = True
            problem_sentences.add(sent_idx)
            if print_sent_idx:
                print(sent_idx, sent.sent_id)
            else:
                print(sent.sent_id)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if " " in word.text:
                if not printed:
                    print("SPACE IN WORD")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a space in it: |%s|\n  Original sentence text was:\n  %s" % (sent.sent_id, sent_idx, word_idx, word.text, sent.text))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if ALLOWED_PUNCT_WORD.match(word.text) and word.upos != "PUNCT":
                if not printed:
                    print("PUNCT WORDS LABELED NON-PUNCT")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a punct word |%s| labeled %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.upos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if not ALLOWED_PUNCT_WORD.match(word.text) and word.upos == "PUNCT":
                if not printed:
                    print("NON PUNCT WORDS LABELED PUNCT")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a non-punct word |%s| labeled %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.upos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word_idx == len(sent.words) - 1:
                continue
            token = word.parent
            if token.spaces_after != '':
                continue
            next_word = sent.words[word_idx+1]
            if word.upos != "PUNCT" and next_word.upos != "PUNCT":
                if not printed:
                    print("UNEXPECTED SpaceAfter=No")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has SpaceAfter=No between two non-punct words" % (sent.sent_id, sent_idx, word_idx))


    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word in sent.words:
            if word.head is None:
                if not printed:
                    print("NO HEAD WORDS")
                    printed = True
                problem_sentences.add(sent_idx)
                if print_sent_idx:
                    print(sent_idx, sent.sent_id, word.id)
                else:
                    print(sent.sent_id, word.id)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word in sent.words:
            if word.deprel is None or word.deprel == "":
                if not printed:
                    print("UNLABELED ARCS")
                    printed = True
                problem_sentences.add(sent_idx)
                if print_sent_idx:
                    print(sent_idx, sent.sent_id, word.id)
                else:
                    print(sent.sent_id, word.id)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        punct = sent.words[-1]
        if punct.upos != "PUNCT":
            continue
        if punct.deprel == 'root':
            if not printed:
                printed = True
                print("PUNCT ROOT")
            problem_sentences.add(sent_idx)
            if print_sent_idx:
                print(sent_idx, sent.sent_id)
            else:
                print(sent.sent_id)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        if sum(x.deprel == 'root' for x in sent.words) > 1:
            if not printed:
                printed = True
                print("MULTIPLE ROOTS")
            problem_sentences.add(sent_idx)
            possible_roots = [(x.text, x.upos, x.id) for x in sent.words if x.deprel == 'root']
            if print_sent_idx:
                print(sent_idx, sent.sent_id, possible_roots)
            else:
                print(sent.sent_id, possible_roots)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        graph = nx.MultiDiGraph()
        for word_idx, word in enumerate(sent.words):
            if word.parent is None or word.deprel is None:
                continue
            graph.add_edge(word.head, word.id, word.deprel)
        try:
            # will throw an error if there is no cycle
            cycle = nx.find_cycle(graph)

            problem_sentences.add(sent_idx)
            if not printed:
                printed = True
                print("CYCLES")
            print("Cycle in sentence %s" % sent.sent_id)
            for edge in cycle:
                print(edge[0], sent.words[edge[0]-1].text, edge[1], sent.words[edge[1]-1].text, edge[2])
        except nx.NetworkXNoCycle:
            pass

    if check_xpos:
        printed = False
        for sent_idx, sent in enumerate(new_doc.sentences):
            for word_idx, word in enumerate(sent.words):
                if not word.xpos or not word.upos:
                    continue
                if word.upos in ALLOWED_UPOS_TO_XPOS:
                    if word.xpos not in ALLOWED_UPOS_TO_XPOS[word.upos]:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("XPOS ERRORS")
                        print("Sentence %s (%d) word %d |%s| had xpos %s which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.xpos, word.upos))
                else:
                    problem_sentences.add(sent_idx)
                    if not printed:
                        printed = True
                        print("XPOS ERRORS")
                    print("Sentence %s (%d) word %d |%s| had unknown upos |%s| with xpos |%s|" % (sent.sent_id, sent_idx, word_idx, word.text, word.upos, word.xpos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.feats == '':
                problem_sentences.add(sent_idx)
                if not printed:
                    printed = True
                    print("BLANK FEAT ERRORS")
                print("Sentence %s (%d) word %d had blank features" % (sent.sent_id, sent_idx, word_idx))

    if check_feats:
        printed = False
        for sent_idx, sent in enumerate(new_doc.sentences):
            for word_idx, word in enumerate(sent.words):
                if not word.upos:
                    continue
                if word.upos not in ALLOWED_UPOS_TO_FEATS:
                    problem_sentences.add(sent_idx)
                    if not printed:
                        printed = True
                        print("FEATURE ERRORS")
                    print("Sentence %s (%d) word %d had an unexpected upos %s with features" % (sent.sent_id, sent_idx, word_idx, word.upos))
                    continue
                if not word.feats or word.feats == '_':
                    if word.upos in DISALLOWED_BLANK_FEATS:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d had blank features, which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx, word.upos))
                    continue
                feat_pieces = word.feats.split("|")
                for feat in feat_pieces:
                    if feat not in ALLOWED_UPOS_TO_FEATS[word.upos]:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d had an unexpected feature %s for upos %s" % (sent.sent_id, sent_idx, word_idx, feat, word.upos))

    return problem_sentences

def main():
    parser = argparse.ArgumentParser(description='Validate a file of SD dependencies & tags')
    parser.add_argument('filename', nargs='+', help='File to validate')
    parser.add_argument('--no_check_xpos', action='store_false', dest='check_xpos', help="Don't check the xpos in the file")
    parser.add_argument('--no_check_feats', action='store_false', dest='check_feats', help="Don't check the feats in the file")
    args = parser.parse_args()

    for filename in args.filename:
        print("Validating %s" % filename)
        new_doc = CoNLL.conll2doc(filename)
        validate(new_doc, check_xpos=args.check_xpos, check_feats=args.check_feats)

if __name__ == '__main__':
    main()
