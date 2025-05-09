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
    "ADP":   ["PSP", "PSPX", "PSPL", "PSPG"],
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
    "ADJ":   ['Case=Acc', 'Case=Nom', 'Case=Voc', 'Degree=Cmp', 'Degree=Pos', 'Degree=Sup', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing'],
    "ADP":   ['Case=Acc', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3'],
    "ADV":   ['Case=Acc', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=3'],
    "AUX":   ['Aspect=Imp', 'Aspect=Perf',
              'AuxType=Be',
              'Gender=Fem', 'Gender=Masc',
              'Mood=Sub',
              'Number=Plur', 'Number=Sing', 'Number[obj]=Sing', 'Number[subj]=Sing',
              'Person=1', 'Person=2', 'Person=3', 'Person[subj]=1', 'Person[subj]=2', 'Person[subj]=3',
              'Polarity=Neg',
              'Tense=Fut', 'Tense=Past', 'Tense=Pres',
              'VerbForm=Inf', 'VerbForm=PresPart',
              'Voice=Pass'],
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
    "VERB":  ['Aspect=Imp', 'Aspect=Perf', 'Aspect=Prog',
              'Case=Acc', 'Case=Nom',
              'Gender=Fem', 'Gender=Masc', 'Gender[obj]=Fem', 'Gender[obj]=Masc', 'Gender[subj]=Fem', 'Gender[subj]=Masc',
              'Mood=Sub',
              'Number=Plur', 'Number=Sing', 'Number[obj]=Plur', 'Number[obj]=Sing', 'Number[subj]=Plur', 'Number[subj]=Sing',
              'Person=1', 'Person=2', 'Person=3', 'Person[obj]=1', 'Person[obj]=2', 'Person[obj]=3', 'Person[subj]=1', 'Person[subj]=2', 'Person[subj]=3',
              'Tense=Fut', 'Tense=Past', 'Tense=Pres',
              'VerbForm=Conv', 'VerbForm=FutPart', 'VerbForm=Inf', 'VerbForm=PastPart', 'VerbForm=PresPart', 'VerbForm=Vnoun',
              'Voice=Act', 'Voice=Pass'],
}

DISALLOWED_BLANK_FEATS = {"NOUN", "PROPN"}

ALLOWED_PUNCT_CHARS = r"؟–؛!\"().۔,-/:،“”"
ALLOWED_PUNCT_WORD = re.compile("[%s]+" % ALLOWED_PUNCT_CHARS)

ADVMOD_EMPH_EXCEPTIONS = {
    """جن جي ڪاوشن سان "وار اينڊ پيس" جهڙا ڪتاب نه رڳو هڪ ٻوليءَ ۾ هڪ قوم لاءِ آهن بلڪه دنيا جي ڪيترين ئي ٻولين ۾، دنيا جي ڪيترن ئي ماڻهن لاءِ آهن ۽ اهو ٻڌائڻ ۾ ڪا شرم جي ڳالهه ناهي ته دنيا جي هر ادب ۾ هومر، دانتي، شيڪسپيئر، گوئٽي، دوستو وسڪي، لوشون، نظامي، خيام، ڪاليداس ۽ ٽئگور لاءِ جڳهه آهي ۽ دنيا جي هر ٻوليءَ ۾ الف ليليٰ دلچسپيءَ سان پڙهيو ويندو آهي،"""
    }


ENFORCED_POS = {
    "مطابق": ["ADP"],
    "جڏهن": ["ADV"],
    "وغيره": ["PART"],
}
for word in ('هجان', 'هجون', 'هجين', 'هجو', 'هجي', 'هجن'):
    ENFORCED_POS[word] = ["AUX"]
for word in ('ھجان', 'ھجون', 'ھجين', 'ھجو', 'ھجي', 'ھجن'):
    ENFORCED_POS[word] = ["AUX"]
ENFORCED_POS['هجئي'] = ["AUX"]
ENFORCED_POS['ڪانهي'] = ["AUX"]
ENFORCED_POS['ھئي'] = ["AUX"]

# the negative polarity AUX words should all be AUX
for word in ['ناهن', 'ناهي', 'ناهيان', 'ناهيون', 'ناھن', 'ناھي', 'ناھيان', 'ناھيون', 'نٿا', 'نٿو', 'نٿي', 'نٿيون', 'ڪونهن', 'ڪونهي', 'ڪونھن', 'ڪونھي']:
    ENFORCED_POS[word] = ["AUX"]

ALLOWED_STRUCTURE = {
    'ها': [('AUX', 'aux'), ('INTJ', 'discourse')],
   'ھا': [('AUX', 'aux'), ('INTJ', 'discourse')],
}

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
                print("Sentence %s (%d) word %d |%s| (line %d) had an unknown upos |%s|" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, word.upos))

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
                print("Sentence %s (%d) word %d has a punct word |%s| (line %d) labeled %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, word.upos))

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
                print("Sentence %s (%d) word %d (line %d) has SpaceAfter=No between two non-punct words" % (sent.sent_id, sent_idx, word_idx, word.line_number))


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
                        print("Sentence %s (%d) word %d |%s| (line %d) had xpos %s which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, word.xpos, word.upos))
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

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.deprel == 'advmod:emph':
                error = None
                if word_idx == 0:
                    error = "Sentence %s (%d) word %d (line %d) had an advmod:emph at the start of the sentence" % (sent.sent_id, sent_idx, word.id, word.line_number)
                elif word.upos != 'PART':
                    error = "Sentence %s (%d) word %d |%s| (line %d) advmod:emph head %d had a UPOS of %s" % (sent.sent_id, sent_idx, word.id, word.text, word.line_number, word.head, word.upos)
                elif word.head > word.id:
                    if sent.text not in ADVMOD_EMPH_EXCEPTIONS:
                        error = "Sentence %s (%d) word %d (line %d) advmod:emph pointed later in the tree, to %d" % (sent.sent_id, sent_idx, word.id, word.line_number, word.head)
                if error is not None:
                    if printed:
                        printed = True
                        print("ADVMOD:EMPH ERRORS")
                    print(error)

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.text in ENFORCED_POS and word.upos not in ENFORCED_POS[word.text]:
                if not printed:
                    printed = True
                    print("Word-specific POS error")
                print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s, which is not in %s" % (sent.sent_id, sent_idx, word.id, word.line_number, word.text, word.upos, ENFORCED_POS[word.text]))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.text in ALLOWED_STRUCTURE:
                structure = (word.pos, word.deprel)
                if structure not in ALLOWED_STRUCTURE[word.text]:
                    if not printed:
                        printed = True
                        print("Found an expected POS & deprel combination")
                    print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s and deprel of %s" % (sent.sent_id, sent_idx, word.id, word.line_number, word.text, word.upos, word.deprel))


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
                    print("Sentence %s (%d) word %d (line %d) had an unexpected upos %s with features" % (sent.sent_id, sent_idx, word_idx, word.line_number, word.upos))
                    continue
                if not word.feats or word.feats == '_':
                    if word.upos in DISALLOWED_BLANK_FEATS:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d (line %d) had blank features, which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx, word.line_number, word.upos))
                    continue
                feat_pieces = word.feats.split("|")
                for feat in feat_pieces:
                    if feat not in ALLOWED_UPOS_TO_FEATS[word.upos]:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d |%s| (line %d) had an unexpected feature %s for upos %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, feat, word.upos))
                if word.upos == 'ADP':
                    feat_map = {x: y for x, y in [x.split("=", maxsplit=2) for x in feat_pieces]}
                    if 'Case' in feat_map:
                        if word.xpos != 'PSPG' and word.xpos != 'PSPX':
                            if not printed:
                                printed = True
                                print("FEATURE ERRORS")
                            print("Sentence %s (%d) word %d |%s| (line %d) had Case=%s but an xpos %s which is not allowed to have Case" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, feat_map['Case'], word.xpos))
                if word.upos == 'VERB':
                    feat_map = {x: y for x, y in [x.split("=", maxsplit=2) for x in feat_pieces]}
                    if 'VerbForm' in feat_map and feat_map['VerbForm'] == 'Inf':
                        if feat_map.get('Aspect') != 'Imp':
                            if not printed:
                                printed = True
                                print("FEATURE ERRORS")
                            print("Sentence %s (%d) word %d |%s| (line %d) had VerbForm=Inf but an Aspect=%s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number, feat_map.get('Aspect')))

    return problem_sentences

def main():
    parser = argparse.ArgumentParser(description='Validate a file of SD dependencies & tags')
    parser.add_argument('filename', nargs='+', help='File to validate')
    parser.add_argument('--no_check_xpos', action='store_false', dest='check_xpos', help="Don't check the xpos in the file")
    parser.add_argument('--no_check_feats', action='store_false', dest='check_feats', help="Don't check the feats in the file")
    args = parser.parse_args()

    for filename in args.filename:
        print("Validating %s" % filename)
        new_doc = CoNLL.conll2doc(filename, keep_line_numbers=True)
        validate(new_doc, check_xpos=args.check_xpos, check_feats=args.check_feats)

if __name__ == '__main__':
    main()
