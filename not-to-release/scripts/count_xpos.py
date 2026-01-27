import argparse
from collections import Counter
import glob

from stanza.utils.conll import CoNLL

parser = argparse.ArgumentParser(description='Which xpos to look for when scanning through the files')
parser.add_argument('xpos', nargs='?', default='PRL', help='Which xpos to make the chart for')
parser.add_argument('--ambiguous', default=False, action='store_true', help='Only output ambiguous')
args = parser.parse_args()

filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt")

pronouns = {}

for filename in filenames:
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            if word.xpos == args.xpos:
                pronouns[word.text] = Counter()

words = sorted(pronouns.keys())
for filename in filenames:
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            if word.text in pronouns:
                pronouns[word.text]["%s/%s" % (word.upos, word.xpos)] += 1

for word in sorted(pronouns):
    if args.ambiguous and len(pronouns[word]) == 1:
        continue
    print(word, pronouns[word])
