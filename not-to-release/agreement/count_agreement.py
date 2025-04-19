from stanza.utils.conll import CoNLL

d1 = CoNLL.conll2doc("det.p1.sarwat.output")
d2 = CoNLL.conll2doc("det.p1.shafi.output")


agree_upos = 0
agree_las = 0
total_words = 0

assert len(d1.sentences) == len(d2.sentences)
for s1, s2 in zip(d1.sentences, d2.sentences):
    assert len(s1.words) == len(s2.words)

    for w1, w2 in zip(s1.words, s2.words):
        total_words += 1
        if w1.upos == w2.upos:
            agree_upos += 1
        if w1.head == w2.head and w1.deprel == w2.deprel:
            agree_las += 1

print("UPOS", agree_upos, total_words, agree_upos / total_words)
print("LAS", agree_las, total_words, agree_las / total_words)
