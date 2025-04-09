import glob
import os

from stanza.utils.conll import CoNLL

dep_filename = "../dependencies/sd_780.conllu"
xpos_filename = "../xpos_features/sd_780_combined.conllu"

dep_doc = CoNLL.conll2doc(dep_filename)
xpos_doc = CoNLL.conll2doc(xpos_filename)

assert len(dep_doc.sentences) == len(xpos_doc.sentences)

for idx, (s1, s2) in enumerate(zip(dep_doc.sentences, xpos_doc.sentences)):
    assert s1.text == s2.text

for idx, (s1, s2) in enumerate(zip(dep_doc.sentences, xpos_doc.sentences)):
    sent_id = "Kawish-20100810-%03d" % (idx+1)
    s1.sent_id = sent_id
    s2.sent_id = sent_id

CoNLL.write_doc2conll(dep_doc, dep_filename)
CoNLL.write_doc2conll(xpos_doc, xpos_filename)
