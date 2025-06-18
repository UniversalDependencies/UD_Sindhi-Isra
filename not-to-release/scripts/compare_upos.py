import argparse

from stanza.utils.conll import CoNLL

ALLOWED_DIFFERENCES = [("DET", "PRON"), ("NOUN", "PROPN")]

def allowed(upos1, upos2):
    if upos1 == upos2:
        return True
    if (upos1, upos2) in ALLOWED_DIFFERENCES:
        return True
    if (upos2, upos1) in ALLOWED_DIFFERENCES:
        return True
    return False

parser = argparse.ArgumentParser(description='Print UPOS deltas between two data files.  Useful for checking where things changed when building new batches')
parser.add_argument('f1', help='File to compare')
parser.add_argument('f2', help='Other file to compare')
parser.add_argument('--save_unchanged', help='Where to save the unchanged sentences')
parser.add_argument('--save_changed', help='Where to save the unchanged sentences')
args = parser.parse_args()

d1 = CoNLL.conll2doc(args.f1)
d2 = CoNLL.conll2doc(args.f2)

assert len(d1.sentences) == len(d2.sentences)

for s1, s2 in zip(d1.sentences, d2.sentences):
    assert len(s1.words) == len(s2.words)

d1_xpos = any(x.xpos for sent in d1.sentences for x in sent.words)
d2_xpos = any(x.xpos for sent in d2.sentences for x in sent.words)
keep_d1 = d1_xpos and not d2_xpos
if keep_d1:
    print("Keeping sentences from %s, as those have xpos and %s does not" % (args.f1, args.f2))

changed = []
unchanged = []

for s1, s2 in zip(d1.sentences, d2.sentences):
    printed = False
    notes = []
    for idx, (w1, w2) in enumerate(zip(s1.words, s2.words)):
        if not allowed(w1.upos, w2.upos):
            if not printed:
                print("{:C}".format(s1))
                print("{:C}".format(s2))
                printed = True
            notes.append((idx+1, "Difference at %d: %s vs %s" % (idx+1, w1.upos, w2.upos)))

    if not printed:
        unchanged.append(s1 if keep_d1 else s2)
    else:
        sent = s1 if keep_d1 else s2
        comments = []
        for note in notes:
            print(note[1])
            comments.append("# NOTE " + note[1])
        comments.append("# highlight tokens " + " ".join([str(note[0]) for note in notes]))
        for comment in comments:
            sent.add_comment(comment)
        changed.append(sent)
        print()

print("%d sentences changed, %d sentences unchanged" % (len(changed), len(unchanged)))

if args.save_unchanged:
    d2.sentences = unchanged
    CoNLL.write_doc2conll(d2, args.save_unchanged)

if args.save_changed:
    d2.sentences = changed
    CoNLL.write_doc2conll(d2, args.save_changed)
