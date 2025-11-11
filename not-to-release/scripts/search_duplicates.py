# Looks through the files in the xpos_features directory for sentences that show up twice
# Ideally nothing is duplicated any more... the output should be empty

import argparse
import glob
import sys

from stanza.utils.conll import CoNLL

duplicates = []

def main():
    known_sentences = set()
    known_text = {}
    text_to_ids = {}

    filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt")
    #filenames = ["duplicates.conllu.3"]
    for filename in filenames:
        doc = CoNLL.conll2doc(filename)
        for sentence in doc.sentences:
            text = sentence.text
            text = text.replace(" ", "")
            sent_id = (filename, sentence.sent_id)
            assert sent_id not in known_sentences, "Found duplicate: %s" % (sent_id,)
            known_sentences.add(sent_id)

            if text in known_text:
                print("Found duplicate!\n  %s\n  %s" % (sent_id, text_to_ids[text]))
                s1 = known_text[text]
                s2 = sentence
                tokens = []
                edges = []
                for w1, w2 in zip(s1.words, s2.words):
                    if w1.pos != w2.pos or w1.xpos != w2.xpos or w1.feats != w2.feats:
                        tokens.append(w1.id)
                    if w1.head != w2.head or w1.deprel != w2.deprel:
                        edges.append(w1.id)
                if len(tokens) == 0 and len(edges) == 0:
                    print("SAME!")
                else:
                    if len(tokens) > 0:
                        tokens_comment = "highlight tokens = %s" % " ".join("%s" % x for x in tokens)
                        s1.add_comment(tokens_comment)
                        s2.add_comment(tokens_comment)
                    if len(edges) > 0:
                        edges_comment = "highlight deprels = %s" % " ".join("%s" % x for x in edges)
                        s1.add_comment(edges_comment)
                        s2.add_comment(edges_comment)
                    duplicates.append(s1)
                    duplicates.append(s2)
            else:
                known_text[text] = sentence
                text_to_ids[text] = sent_id

    doc.sentences = duplicates
    if len(doc.sentences) > 0:
        CoNLL.write_doc2conll(doc, "duplicates.conllu")


if __name__ == '__main__':
    main()
