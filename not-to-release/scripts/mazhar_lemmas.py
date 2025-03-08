"""
Find overlaps between the lemmas in the Mazhar Dootio dataset and the ISRA dataset text
"""

from collections import Counter
from collections import defaultdict
from operator import itemgetter
import glob

from stanza.utils.conll import CoNLL

base_filename = "extern_data/ud2/git/UD_Sindhi-MazharDootio/sd_mazhardootio-ud-test.conllu"
base_dataset = CoNLL.conll2doc(base_filename)

word_upos_to_lemma = defaultdict(set)
for sentence in base_dataset.sentences:
    for word in sentence.words:
        pair = (word.text, word.upos)
        word_upos_to_lemma[pair].add(word.lemma)

filtered_word_upos = {}
for word, upos in word_upos_to_lemma.keys():
    if len(word_upos_to_lemma[word, upos]) != 1:
        print("Conflict: %s %s %s" % (word, upos, word_upos_to_lemma[word, upos]))
    else:
        filtered_word_upos[(word, upos)] = list(word_upos_to_lemma[word, upos])[0]

print("%d known combinations" % len(filtered_word_upos))

target_pairs = Counter()

unknown_pairs = Counter()

upos_files = glob.glob("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/dependencies/*")
for filename in upos_files:
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            pair = (word.text, word.upos)
            if pair in filtered_word_upos:
                target_pairs[pair] += 1
            else:
                unknown_pairs[pair] += 1

candidate_lemmas = [(word, upos, filtered_word_upos[word, upos]) for word, upos in target_pairs if (word, upos) in filtered_word_upos]
print("%d words in our dataset known in MD dataset" % len(candidate_lemmas))
print("%d words unknown" % len(unknown_pairs))
candidate_lemmas.sort(key=itemgetter(1, 0))
print("LEMMAS FROM MAZHAR DOOTIO")
print("-------------------------")
for word, upos, lemma in candidate_lemmas:
    print("%s\t%s\t%s" % (word, upos, lemma))

print("LEMMAS CURRENTLY UNKNOWN")
print("------------------------")
common_unknown = [x[0] for x in unknown_pairs.most_common(1000) if x[0][1] != 'PUNCT']
common_unknown.sort(key=itemgetter(1, 0))
for word, upos in common_unknown:
    print("%s\t%s\t%s" % (word, upos, word))
# TODO
