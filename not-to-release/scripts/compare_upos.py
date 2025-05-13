import argparse

from stanza.utils.conll import CoNLL

parser = argparse.ArgumentParser(description='Print UPOS deltas between two data files.  Useful for checking where things changed when building new batches')
parser.add_argument('f1', help='File to compare')
parser.add_argument('f2', help='Other file to compare')
parser.add_argument('--save_unchanged', help='Where to save the unchanged sentences')
args = parser.parse_args()

d1 = CoNLL.conll2doc(args.f1)
d2 = CoNLL.conll2doc(args.f2)

assert len(d1.sentences) == len(d2.sentences)

for s1, s2 in zip(d1.sentences, d2.sentences):
    assert len(s1.words) == len(s2.words)

changed = []
unchanged = []

for s1, s2 in zip(d1.sentences, d2.sentences):
    printed = False
    for idx, (w1, w2) in enumerate(zip(s1.words, s2.words)):
        if w1.upos != w2.upos:
            if not printed:
                print("{:C}".format(s1))
                print("{:C}".format(s2))
                printed = True
            print("Difference at %d: %s vs %s" % (idx+1, w1.upos, w2.upos))

    if not printed:
        unchanged.append(s2)
    else:
        changed.append(s2)
        print()

print("%d sentences changed, %d sentences unchanged" % (len(changed), len(unchanged)))

if args.save_unchanged:
    d2.sentences = unchanged
    CoNLL.write_doc2conll(d2, args.save_unchanged)
