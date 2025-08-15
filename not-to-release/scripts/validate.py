import argparse
from collections import namedtuple
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
    "ADJ":   ['Case=Acc', 'Case=Nom', 'Case=Voc',
              'Degree=Cmp', 'Degree=Pos', 'Degree=Sup',
              'Gender=Fem', 'Gender=Masc',
              'Number=Plur', 'Number=Sing',
              'PronType=Tot'],
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
              'Typo=Yes',
              'VerbForm=Inf', 'VerbForm=PresPart',
              'Voice=Act', 'Voice=Pass'],  # TODO: not sure this is correct, but the validator nagging is annoying
    "CCONJ": [],
    "DET":   ['Case=Acc', 'Case=Gen', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=1', 'Person=3'],
    "INTJ":  [],
    "NOUN":  ['Case=Abl', 'Case=Acc', 'Case=Nom', 'Case=Voc',
              'ExtPos=ADV',
              'Gender=Fem', 'Gender=Masc',
              'Number=Plur', 'Number=Sing',
              'Person=3'],
    "NUM":   ['Case=Acc', 'Case=Nom', 'Number=Plur', 'Number=Sing'],
    "PART":  ['PartType=Emp'],
    "PRON":  ['Case=Acc', 'Case=Gen', 'Case=Nom', 'Gender=Fem', 'Gender=Masc', 'Number=Plur', 'Number=Sing', 'Person=1', 'Person=2', 'Person=3'],
    "PROPN": ['Case=Abl', 'Case=Acc', 'Case=Nom', 'Case=Voc', 'Gender=Fem', 'Gender=Masc', 'Number=Sing'],
    "PUNCT": [],
    "SCONJ": [],
    "SYM":   [],
    "VERB":  ['Aspect=Imp', 'Aspect=Perf', 'Aspect=Prog',
              'Case=Acc', 'Case=Nom',
              'Case[obj]=Acc', 'Case[subj]=Acc', 'Case[subj]=Nom', # TODO: resplit these into MWT?
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


ENFORCED_FEATURES = {}

ENFORCED_POS_XPOS = {}
ENFORCED_POS = {
    "جڏهن": ["ADV"],
    "وغيره": ["PART"],
    "آخر": ["ADV", "NOUN"],
    "ٿورو": ["ADJ"],
}
for word in ('هجان', 'هجون', 'هجين', 'هجو', 'هجي', 'هجن'):
    ENFORCED_POS[word] = ["AUX"]
for word in ('ھجان', 'ھجون', 'ھجين', 'ھجو', 'ھجي', 'ھجن'):
    ENFORCED_POS[word] = ["AUX"]
for word in ('ہجان', 'ہجون', 'ہجين', 'ہجو', 'ہجي', 'ہجن'):
    ENFORCED_POS[word] = ["AUX"]
for word in ('ٿيندو', 'ٿيندا', 'ٿيندي', 'ٿينديون'):
    ENFORCED_POS[word] = ["VERB"]
ENFORCED_POS['هجئي'] = ["AUX"]
ENFORCED_POS['ڪانهي'] = ["AUX"]
ENFORCED_POS['ھئي'] = ["AUX"]

for word in ('مطابق', 'سواءِ', 'بنان', 'بغير', 'لاءِ'):
    ENFORCED_POS_XPOS[word] = [('ADP', 'PSP')]

can_could_aux = []
# can/could AUX words
can_could_aux.extend(['سگهيا', 'سگهندين', 'سگهن', 'سگهان', 'سگهيون', 'سگهيو', 'سگهين', 'سگهيا', 'سگهون', 'سگهڻ', 'سگهندي', 'سگهندو', 'سگهن', 'سگهجي', 'سگهان'])
can_could_aux.extend(['سگهي', 'سگهنديس', 'سگهندس', 'سگهندا', 'سگهنداسون', 'سگهنداسين', 'سگهنديون', 'سگهيس', 'سگهبو'])
# variant spellings of the above
can_could_aux.extend(['سگھيا', 'سگھندين', 'سگھن', 'سگھان', 'سگھيون', 'سگھيو', 'سگھين', 'سگھيا', 'سگھون', 'سگھڻ', 'سگھندي', 'سگھندو', 'سگھن', 'سگھجي', 'سگھان'])
can_could_aux.extend(['سگھي', 'سگھنديس', 'سگھندس', 'سگھندا', 'سگھنداسون', 'سگھنداسين', 'سگھنديون', 'سگھيس', 'سگھبو'])

for word in can_could_aux:
    ENFORCED_POS[word] = ['AUX']
# this one has an exception in the treebank
ENFORCED_POS['سگهو'] = ['AUX', 'ADV']

ENFORCED_FEATURES['سگهان'] = ['Person=1', 'Number=Sing']
ENFORCED_FEATURES['سگهون'] = ['Person=1', 'Number=Plur']
ENFORCED_FEATURES['سگهين'] = ['Person=2', 'Number=Sing']
# TODO can be AUX or ADV?
# ENFORCED_FEATURES['سگهو'] = ['Person=2', 'Number=Plur']
ENFORCED_FEATURES['سگهي'] = ['Person=3', 'Number=Sing']
ENFORCED_FEATURES['سگهن'] = ['Person=3', 'Number=Plur']

ENFORCED_POS['ڄڻ'] = ['PRON']

ENFORCED_POS_XPOS['ڪڏهن'] = [('ADV', 'ADT')]

for word in ("اھڙيءَ","اھڙن","اھڙي","اھڙو","اھڙا","اھڙيون","اھڙين","اهڙيءَ","اهڙن","اهڙي","اهڙو","اهڙا","اهڙيون","اهڙين"):
    ENFORCED_POS[word] = ['DET', 'ADJ']

ENFORCED_POS['گذريل'] = ['VERB']

# demonstratives
demonstratives = ['ان', 'اِهو', 'انهي', 'انھي', 'انهيءِ', 'اِهو', 'اِهي', 'اھا', 'اھڙو', 'اھي', 'ڪوبه', 'هرڪوئي', 'هِن', 'هُوءَ', 'ھن', 'اُهو', 'اهي', 'اهو', 'اِها']
demonstratives.extend(['اُها', 'اها', 'انهيءَ'])
for word in demonstratives:
    ENFORCED_POS_XPOS[word] = [('DET', 'PRD')]

# the negative polarity AUX words should all be AUX
for word in ['ڪانهي', 'ڪانھي', 'ناهن', 'ناهي', 'ناهيان', 'ناهيون', 'ناھن', 'ناھي', 'ناھيان', 'ناھيون', 'نٿا', 'نٿو', 'نٿي', 'نٿيون', 'ڪونهن', 'ڪونهي', 'ڪونھن', 'ڪونھي']:
    ENFORCED_POS[word] = ["AUX"]
    ENFORCED_FEATURES[word] = ["Polarity=Neg"]

ENFORCED_POS['توڙي'] = ['CCONJ']
ENFORCED_POS['۽'] = ['CCONJ']

ENFORCED_POS['ڪٿي'] = ['ADV']

ENFORCED_POS['ٻئي'] = ['ADJ']    # both
for word in ('ھڪ', 'هڪ'):   # one
    ENFORCED_POS[word] = ['NUM']
ENFORCED_POS['ٻن'] = ['NUM'] # two, Case=Acc
ENFORCED_FEATURES['ٻن'] = ['Case=Acc']
ENFORCED_POS['هزارن'] = ['NUM'] # thousands, Case=Acc
ENFORCED_FEATURES['هزارن'] = ['Case=Acc', 'Number=Plur']
ENFORCED_POS['لکن'] = ['NUM', 'VERB'] # millions, Case=Acc, can also be VERB
ENFORCED_FEATURES[('لکن', 'NUM')] = ['Case=Acc', 'Number=Plur']

ENFORCED_POS_XPOS['۾'] = [('ADP', 'PSPL')]
ENFORCED_POS_XPOS['ڪيئن'] = [('ADV', 'ADM'), ('PRON', 'PRWH')]
ENFORCED_POS_XPOS['پوءِ'] = [('ADP', 'PSP'), ('ADV', 'ADT'), ('SCONJ', 'CS')]
ENFORCED_POS_XPOS['شايد'] = [('ADV', 'ADM')]
# Can rarely be ADV but in all the reviewed examples this is ADP/PSP
ENFORCED_POS_XPOS['وانگر'] = [('ADP', 'PSP')]
ENFORCED_POS_XPOS['جنهنڪري'] = [('ADV', 'ADV'), ('SCONJ', 'CS')]
ENFORCED_POS_XPOS['هاڻي'] = [('ADV', 'ADT')]
ENFORCED_POS_XPOS['جيئن'] = [('ADV', 'ADM'), ('PRON', 'PRL')]

# two inflections of 'all'
ENFORCED_POS_XPOS['سڀني'] = [('ADJ', 'JJ')]  # updated all JJO -> JJ
ENFORCED_FEATURES['سڀني'] = ["Case=Acc", "PronType=Tot"]
ENFORCED_POS_XPOS['سڀئي'] = [('ADJ', 'JJ')]
ENFORCED_FEATURES['سڀئي'] = ["Case=Nom", "PronType=Tot"]

ALLOWED_STRUCTURE = {
    'ها': [('AUX', 'aux'), ('INTJ', 'discourse')],
   'ھا': [('AUX', 'aux'), ('INTJ', 'discourse')],
}

ALLOWED_STRUCTURE['وغيره'] = [('PART', 'conj')]
ALLOWED_STRUCTURE['جيڪڏهن'] = [('SCONJ', 'mark')]

ALLOWED_STRUCTURE['۾'] = [('ADP', 'mark'), ('ADP', 'case')]
ALLOWED_STRUCTURE['بلڪه'] = [('SCONJ', 'mark')]
ALLOWED_STRUCTURE['جنهنڪري'] = [('ADV', 'advmod'), ('SCONJ', 'mark')]
ALLOWED_STRUCTURE['هاڻي'] = [('ADV', 'advmod')]
ALLOWED_STRUCTURE['تنهنڪري'] = [('SCONJ', 'mark')]
ALLOWED_STRUCTURE['بلڪ'] = [('SCONJ', 'mark')]
ALLOWED_STRUCTURE['جيڪڏھن'] = [('SCONJ', 'mark')]

# this word can potentially also be ADJ, but that is not attested in the dataset
ENFORCED_POS_XPOS['آڏو'] = [('ADP', 'PSP'), ('ADV', 'ADP')]
ALLOWED_STRUCTURE['آڏو'] = [('ADP', 'case'), ('ADV', 'advmod')]

DISALLOWED_UPOS_RELATIONS = {
    "ADP": ["nmod", "advcl", "amod"],
    "CCONJ": ["advmod"],
    "PART": ["case"],
}

DISALLOWED_XPOS_RELATIONS = {
    "PSP": ["obj"],
    "PSPL": ["obj"],
    "PSPG": ["obj"],
}

ENFORCED_RELATION_UPOS = {
    "advmod:emph": ["PART"],
}

# various inflections of هڪڙو / one
for word in ('هڪڙو', 'ھڪڙو'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC'), ('PROPN', 'NNP')]
    ENFORCED_FEATURES[(word, 'ADJ')] = ["Case=Nom", "Number=Sing", "Gender=Masc"]
# ambiguous between Nom/Acc and Masc/Fem
for word in ('ھڪڙي', 'هڪڙي'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Number=Sing"]
# currently not attested anywhere in the dataset
for word in ('ھڪڙا', 'هڪڙا'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Case=Nom", "Number=Plur", "Gender=Masc"]
# currently not attested anywhere in the dataset
for word in ('ھڪڙن', 'هڪڙن'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Case=Acc", "Number=Plur", "Gender=Masc"]
# can be ambiguous between Nom/Acc
for word in ('هڪڙيء', 'هڪڙيءَ', 'ھڪڙيء', 'ھڪڙيءَ'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Number=Sing", "Gender=Fem"]
# currently not attested anywhere in the dataset
for word in ('هڪڙيون', 'هڪڙيونءَ', 'هڪڙيونء', 'ھڪڙيونء', 'ھڪڙيونءَ', 'ھڪڙيون'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Case=Nom", "Number=Plur", "Gender=Fem"]
# currently not attested anywhere in the dataset
for word in ('ھڪڙين', 'هڪڙين'):
    ENFORCED_POS_XPOS[word] = [('ADJ', 'JJC')]
    ENFORCED_FEATURES[word] = ["Case=Acc", "Number=Plur", "Gender=Fem"]

# Depending on the context, جلد can be noun or adverb. As ADV, it should always be ADM.
ENFORCED_POS_XPOS['جلد'] = [('ADV', 'ADM'), ('NOUN', 'NN')]

# We keep a list of fixed expressions where we expect each occurrence of the words in order
# to have the deprel fixed and the listed UPOS/ExtPos.  
FixedExpression = namedtuple('FixedExpression', 'words extpos')
FIXED_EXPRESSIONS = []
FIXED_EXPRESSIONS.append(FixedExpression((('ڏينهون', 'NOUN'), ('ڏينهن', 'NOUN')), 'ADV'))

def check_fixed(new_doc, check_feats):
    problem_sentences = set()
    printed = False

    for fixed_expression in FIXED_EXPRESSIONS:
        for sent_idx, sent in enumerate(new_doc.sentences):
            for word_idx, word in enumerate(sent.words):
                # check that the span exists and the words in this span are the words of the fixed expression
                span = sent.words[word_idx:word_idx+len(fixed_expression.words)]
                if len(span) < len(fixed_expression.words):
                    continue
                if any(w.text != fw[0] for w, fw in zip(span, fixed_expression.words)):
                    continue

                # we now know the word texts match the expected fixed words
                # check the POS of the words in this span
                errors = []
                if not all(w.pos == fw[1] for w, fw in zip(span, fixed_expression.words)):
                    words = ", ".join("%s_%s" % fw for fw in fixed_expression.words)
                    errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) did not follow expected POS: %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, words))
                # check the deprel of the words after the first
                for fixed_word in span[1:]:
                    if fixed_word.head != word_idx+1:
                        errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) had head %s instead of %d" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, fixed_word.head, word_idx+1))
                    if fixed_word.deprel != 'fixed':
                        errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) had deprel %s instead of fixed" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, fixed_word.deprel))
                # if checking features, look for the correct ExtPos or flag an error
                if check_feats:
                    if not span[0].feats or span[0].feats == '_':
                        errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) did not have an ExtPos; expected %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, fixed_expression.extpos))
                    else:
                        feats = span[0].feats.split("|")
                        for feat in feats:
                            if feat.startswith("ExtPos="):
                                if feat.split("=", 1)[1] != fixed_expression.extpos:
                                    errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) had %s; expected %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, feat, fixed_expression.extpos))
                                break
                        else:
                            errors.append("Sentence %s (%d) fixed expression starting at word %d (line %d) had features %s, with no ExtPos; expected %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, span[0].feats, fixed_expression.extpos))
                if len(errors) > 0:
                    if not printed:
                        print("FIXED EXPRESSION ERROR")
                        printed = True
                    problem_sentences.add(sent_idx)
                    for error in errors:
                        print(error)

    return problem_sentences

def check_unknown_upos(new_doc):
    problem_sentences = set()
    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.upos not in ALLOWED_UPOS:
                if not printed:
                    print("UNKNOWN UPOS")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d |%s| (line %d) had an unknown upos |%s|" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number+1, word.upos))
    return problem_sentences

def check_no_root_sentences(new_doc):
    problem_sentences = set()
    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        if not any(word.deprel == 'root' for word in sent.words):
            if not printed:
                print("NO ROOT SENTENCES")
                printed = True
            problem_sentences.add(sent_idx)
            print("Sentence %d |%s| has no root" % (sent_idx, sent.sent_id))
    return problem_sentences

def check_space_in_word(new_doc):
    problem_sentences = set()
    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if " " in word.text:
                if not printed:
                    print("SPACE IN WORD")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a space in it: |%s|\n  Original sentence text was:\n  %s" % (sent.sent_id, sent_idx, word_idx, word.text, sent.text))
    return problem_sentences

def check_punct_word_labels(new_doc):
    problem_sentences = set()
    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if ALLOWED_PUNCT_WORD.match(word.text) and word.upos != "PUNCT":
                if not printed:
                    print("PUNCT WORDS LABELED NON-PUNCT")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a punct word |%s| (line %d) labeled %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number+1, word.upos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if not ALLOWED_PUNCT_WORD.match(word.text) and word.upos == "PUNCT":
                if not printed:
                    print("NON PUNCT WORDS LABELED PUNCT")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d has a non-punct word |%s| labeled %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.upos))

    return problem_sentences

def check_pos_deprel_happiness(new_doc, check_xpos):
    problem_sentences = set()
    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.text in ALLOWED_STRUCTURE:
                structure = (word.pos, word.deprel)
                if structure not in ALLOWED_STRUCTURE[word.text]:
                    if not printed:
                        printed = True
                        print("Found an unexpected POS & deprel combination")
                    problem_sentences.add(sent_idx)
                    print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s and deprel of %s.  Expected: %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.upos, word.deprel, ALLOWED_STRUCTURE[word.text]))

    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.upos in DISALLOWED_UPOS_RELATIONS and word.deprel in DISALLOWED_UPOS_RELATIONS[word.upos]:
                if not printed:
                    printed = True
                    print("Found an unexpected POS & deprel combination")
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s and deprel of %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.upos, word.deprel))
            if check_xpos and word.xpos in DISALLOWED_XPOS_RELATIONS and word.deprel in DISALLOWED_XPOS_RELATIONS[word.xpos]:
                if not printed:
                    printed = True
                    print("Found an unexpected POS & deprel combination")
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d (line %d) is |%s| with an XPOS of %s and deprel of %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.xpos, word.deprel))

    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            for deprel, allowed_upos in ENFORCED_RELATION_UPOS.items():
                if word.deprel == deprel and word.upos not in allowed_upos:
                    if not printed:
                        printed = True
                        print("Found an unexpected POS & deprel combination")
                    problem_sentences.add(sent_idx)
                    print("Sentence %s (%d) word %d (line %d, |%s|) has a UPOS of %s and deprel of %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.upos, word.deprel))


    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            # search for VERB/obj combinations
            # generally these are wrong, but we allow it if the following word is a specific ADP
            if word.upos != 'VERB' or word.deprel != 'obj':
                continue
            error = True
            if word_idx + 1 < len(sent.words):
                next_word = sent.words[word_idx+1]
                if next_word.upos == 'ADP' and next_word.text in ('واري', 'وارين', 'وارن', 'وارو'):
                    error = False
            if error:
                if not printed:
                    printed = True
                    print("Found an unexpected POS & deprel combination")
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s and deprel of %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.upos, word.deprel))

    return problem_sentences

def check_unexpected_space_after(new_doc):
    problem_sentences = set()
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
    return problem_sentences

def check_xpos_required(new_doc, check_xpos, require_xpos):
    problem_sentences = set()
    if not check_xpos or not require_xpos:
        return problem_sentences

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.xpos is None:
                if not printed:
                    print("WORD WITH NO XPOS")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) word %d (line %d) has no xpos" % (sent.sent_id, sent_idx, word_idx, word.line_number))
    return problem_sentences

def check_pos_xpos_happiness(new_doc, check_xpos):
    problem_sentences = set()
    if not check_xpos:
        return problem_sentences

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            allowed = ENFORCED_POS_XPOS.get(word.text)
            if not allowed:
                continue
            if (word.upos, word.xpos) not in allowed:
                if not printed:
                    print("WORD WITH INCOMPATIBLE UPOS/XPOS")
                    printed = True
                problem_sentences.add(sent_idx)
                allowed = ", ".join(["/".join(x) for x in allowed])
                print("Sentence %s (%d) word %d |%s| (line %d) has incompatible upos/xpos %s/%s.  Expected is %s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number+1, word.upos, word.xpos, allowed))
    return problem_sentences

def check_missing_heads(new_doc):
    problem_sentences = set()

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word in sent.words:
            if word.head is None:
                if not printed:
                    print("NO HEAD WORDS")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) has a word %s (line %d) with no head" % (sent.sent_id, sent_idx, word.id, word.line_number))

    return problem_sentences

def check_missing_deprel(new_doc):
    problem_sentences = set()

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word in sent.words:
            if word.deprel is None or word.deprel == "":
                if not printed:
                    print("UNLABELED ARCS")
                    printed = True
                problem_sentences.add(sent_idx)
                print("Sentence %s (%d) has a word %s (line %d) with no deprel" % (sent.sent_id, sent_idx, word.id, word.line_number))

    return problem_sentences

def check_th_words(new_doc, check_xpos):
    """
    Currently we have the words هين and هون annotated to be compound words of a NUM before them.  This checks those relations and the POS
    """
    problem_sentences = set()
    errors = []
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.text != 'هين' and word.text != 'هون':
                continue
            new_errors = []
            if word.upos != 'PART':
                new_errors.append("Sentence %s (%d) word %d |%s| (line %d) has upos %s.  Expected PART" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.upos))
            if check_xpos and word.xpos != 'PART':
                new_errors.append("Sentence %s (%d) word %d |%s| (line %d) has xpos %s.  Expected PART" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.xpos))
            if word.deprel != 'compound':
                new_errors.append("Sentence %s (%d) word %d |%s| (line %d) has deprel %s.  Expected all -th words to have compound" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.deprel))
            if word.head != word_idx:   # heads indexed by 1, enumerate indexed by 0
                new_errors.append("Sentence %s (%d) word %d |%s| (line %d) attached to %d.  Expected all -th words to attach to the previous word." % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.head))
            else:
                head = sent.words[word.head-1]
                if head.upos != 'NUM':
                    new_errors.append("Sentence %s (%d) word %d |%s| (line %d) attached to %d |%s| with a POS of %s.  Expected all -th words to attach to NUM." % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.head, head.text, head.upos))
                if head.deprel != 'amod':
                    new_errors.append("Sentence %s (%d) word %d |%s| (line %d) attached to %d |%s| with a deprel of %s.  Expected all -th words to attach to an amod." % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.head, head.text, head.deprel))
            if len(new_errors) > 0:
                errors.extend(new_errors)
                problem_sentences.add(sent_idx)
    if len(errors) > 0:
        print("ERRORS ON -TH WORDS")
        for error in errors:
            print(error)
    return problem_sentences

def validate(new_doc, check_xpos=True, check_feats=True, require_xpos=True):
    problem_sentences = set()

    problem_sentences |= check_unknown_upos(new_doc)
    problem_sentences |= check_no_root_sentences(new_doc)
    problem_sentences |= check_space_in_word(new_doc)
    problem_sentences |= check_punct_word_labels(new_doc)
    problem_sentences |= check_pos_deprel_happiness(new_doc, check_xpos)
    problem_sentences |= check_unexpected_space_after(new_doc)
    problem_sentences |= check_xpos_required(new_doc, check_xpos, require_xpos)
    problem_sentences |= check_pos_xpos_happiness(new_doc, check_xpos)
    problem_sentences |= check_fixed(new_doc, check_feats)
    problem_sentences |= check_missing_heads(new_doc)
    problem_sentences |= check_missing_deprel(new_doc)
    problem_sentences |= check_th_words(new_doc, check_xpos)

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
            print("Sentence %s (%d) has a punct word as the root" % (sent.sent_id, sent_idx))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        if sum(x.deprel == 'root' for x in sent.words) > 1:
            if not printed:
                printed = True
                print("MULTIPLE ROOTS")
            problem_sentences.add(sent_idx)
            possible_roots = [(x.text, x.upos, x.id) for x in sent.words if x.deprel == 'root']
            print("Sentence %s (%d) has multiple roots: %s" % (sent.sent_id, sent_idx, possible_roots))

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
                        print("Sentence %s (%d) word %d |%s| (line %d) had xpos %s which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, word.xpos, word.upos))
                else:
                    problem_sentences.add(sent_idx)
                    if not printed:
                        printed = True
                        print("XPOS ERRORS")
                    print("Sentence %s (%d) word %d |%s| had unknown upos |%s| with xpos |%s|" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.upos, word.xpos))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.feats == '':
                problem_sentences.add(sent_idx)
                if not printed:
                    printed = True
                    print("BLANK FEAT ERRORS")
                print("Sentence %s (%d) word %d had blank features" % (sent.sent_id, sent_idx, word_idx+1))

    printed = False
    for sent_idx, sent in enumerate(new_doc.sentences):
        for word_idx, word in enumerate(sent.words):
            if word.deprel == 'advmod:emph':
                error = None
                if word_idx == 0:
                    error = "Sentence %s (%d) word %d (line %d) had an advmod:emph at the start of the sentence" % (sent.sent_id, sent_idx, word.id, word.line_number)
                elif word.upos != 'PART':
                    error = "Sentence %s (%d) word %d |%s| (line %d) advmod:emph head %d had a UPOS of %s" % (sent.sent_id, sent_idx, word.id, word.text, word.line_number+1, word.head, word.upos)
                elif word.head > word.id:
                    if sent.text not in ADVMOD_EMPH_EXCEPTIONS:
                        error = "Sentence %s (%d) word %d (line %d) advmod:emph pointed later in the tree, to %d" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.head)
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
                print("Sentence %s (%d) word %d (line %d) is |%s| with a POS of %s, which is not in %s" % (sent.sent_id, sent_idx, word.id, word.line_number+1, word.text, word.upos, ENFORCED_POS[word.text]))

    if check_feats:
        printed = False
        for sent_idx, sent in enumerate(new_doc.sentences):
            for word_idx, word in enumerate(sent.words):
                expected_features = ENFORCED_FEATURES.get(word.text)
                if expected_features is None:
                    expected_features = ENFORCED_FEATURES.get((word.text, word.upos))
                if expected_features is None:
                    continue

                error = ""
                if not word.feats or word.feats == '_':
                    error = "Sentence %s (%d) word %d (line %d) |%s| had blank features, but this word is expected to have %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, word.text, expected_features)
                else:
                    pieces = word.feats.split("|")
                    for expected in expected_features:
                        if expected not in pieces:
                            error = "Sentence %s (%d) word %d (line %d) |%s| did not have required feature %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, word.text, expected)
                if error:
                    if not printed:
                        printed = True
                        print("EXPECTED FEATURES MISSING")
                    print(error)

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
                    print("Sentence %s (%d) word %d (line %d) had an unexpected upos %s with features" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, word.upos))
                    continue
                if not word.feats or word.feats == '_':
                    if word.upos in DISALLOWED_BLANK_FEATS:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d (line %d) had blank features, which is not allowed for upos %s" % (sent.sent_id, sent_idx, word_idx+1, word.line_number+1, word.upos))
                    continue
                feat_pieces = word.feats.split("|")
                for feat in feat_pieces:
                    if feat not in ALLOWED_UPOS_TO_FEATS[word.upos]:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d |%s| (line %d) had an unexpected feature %s for upos %s" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, feat, word.upos))
                for feat in feat_pieces:
                    if len(feat.split("=")) <= 1:
                        problem_sentences.add(sent_idx)
                        if not printed:
                            printed = True
                            print("FEATURE ERRORS")
                        print("Sentence %s (%d) word %d |%s| (line %d) had an incomplete feature, not key=value: %s" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, feat))
                        continue
                if word.upos == 'ADP':
                    feat_map = {x: y for x, y in [x.split("=", maxsplit=1) for x in feat_pieces]}
                    if 'Case' in feat_map:
                        if word.xpos != 'PSPG' and word.xpos != 'PSPX':
                            if not printed:
                                printed = True
                                print("FEATURE ERRORS")
                            print("Sentence %s (%d) word %d |%s| (line %d) had Case=%s but an xpos %s which is not allowed to have Case" % (sent.sent_id, sent_idx, word_idx+1, word.text, word.line_number+1, feat_map['Case'], word.xpos))
                if word.upos == 'VERB':
                    feat_map = {x: y for x, y in [x.split("=", maxsplit=1) for x in feat_pieces]}
                    if 'VerbForm' in feat_map and feat_map['VerbForm'] == 'Inf':
                        if feat_map.get('Aspect') != 'Imp':
                            if not printed:
                                printed = True
                                print("FEATURE ERRORS")
                            print("Sentence %s (%d) word %d |%s| (line %d) had VerbForm=Inf but an Aspect=%s" % (sent.sent_id, sent_idx, word_idx, word.text, word.line_number+1, feat_map.get('Aspect')))

    return problem_sentences

def main():
    parser = argparse.ArgumentParser(description='Validate a file of SD dependencies & tags')
    parser.add_argument('filename', nargs='+', help='File to validate')
    parser.add_argument('--no_check_xpos', action='store_false', dest='check_xpos', help="Don't check the xpos in the file")
    parser.add_argument('--no_require_xpos', action='store_false', dest='require_xpos', help="Don't require that all words have xpos")
    parser.add_argument('--no_check_feats', action='store_false', dest='check_feats', help="Don't check the feats in the file")
    args = parser.parse_args()

    for filename in args.filename:
        print("Validating %s" % filename)
        new_doc = CoNLL.conll2doc(filename, keep_line_numbers=True)
        validate(new_doc, check_xpos=args.check_xpos, check_feats=args.check_feats)

if __name__ == '__main__':
    main()
