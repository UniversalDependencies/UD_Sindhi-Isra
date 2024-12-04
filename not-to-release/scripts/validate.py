import sys

import networkx as nx

from stanza.utils.conll import CoNLL

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

def validate(new_doc, print_sent_idx=False):
    problem_sentences = set()

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
            cycle = nx.find_cycle(graph)
            if not printed:
                printed = True
                print("CYCLES")
            print("Cycle in sentence %s" % sent.sent_id)
            for edge in cycle:
                print(edge[0], sent.words[edge[0]-1].text, edge[1], sent.words[edge[1]-1].text, edge[2])
        except nx.NetworkXNoCycle:
            pass

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if not word.xpos or not word.upos:
                continue
            if word.upos in ALLOWED_UPOS_TO_XPOS:
                if word.xpos not in ALLOWED_UPOS_TO_XPOS[word.upos]:
                    if not printed:
                        printed = True
                        print("XPOS ERRORS")
                    print("Sentence %s (%d) word %d |%s| had xpos %s which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.xpos, word.upos))
            else:
                if not printed:
                    printed = True
                    print("XPOS ERRORS")
                print("Sentence %s (%d) word %d |%s| had unknown upos |%s| with xpos |%s|" % (sent.sent_id, sent_idx, word_idx, word.text, word.upos, word.xpos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.feats == '':
                if not printed:
                    printed = True
                    print("FEAT ERRORS")
                print("Sentence %s word %d had blank features" % (sent_idx, word_idx))

    return problem_sentences

def main():
    new_doc = CoNLL.conll2doc(sys.argv[1])
    validate(new_doc)

if __name__ == '__main__':
    main()
