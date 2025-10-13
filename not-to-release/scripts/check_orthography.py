import glob
from stanza.utils.conll import CoNLL

from collections import Counter, defaultdict


def get_filenames():
    filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt")
    return filenames

c1 = "ه"
c2 = "ہ"
c3 = "ھ"

def count_words(filename):
    doc = CoNLL.conll2doc(filename)
    words = defaultdict(Counter)
    for sent in doc.sentences:
        for word in sent.words:
            text = word.text
            if c1 in text:
                marker = "c1"
            elif c2 in text:
                marker = "c2"
            elif c3 in text:
                marker = "c3"
            else:
                continue
            base = text.replace(c2, c1).replace(c3, c1)
            words[base][marker + ":" + word.text] += 1
    return words

def main():
    filenames = get_filenames()

    results = defaultdict(Counter)

    for filename in filenames:
        words = count_words(filename)
        for word in words:
            results[word] += words[word]

    for word in sorted(results):
        counts = results[word]
        print("Normalized: %s" % word)
        for version in counts:
            print("  %s: %d" % (version, counts[version]))

if __name__ == '__main__':
    main()
