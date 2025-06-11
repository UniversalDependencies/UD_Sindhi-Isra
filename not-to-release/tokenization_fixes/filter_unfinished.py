from stanza.utils.conll import CoNLL

import glob

full_tokenized = CoNLL.conll2doc("../dependencies/sd_batch_2_1000.conllu")
retagged_ids = set()

for filename in glob.glob("../xpos_features/sd_batch_2*"):
    already_tagged = CoNLL.conll2doc(filename)
    retagged_ids = retagged_ids.union([sent.sent_id for sent in already_tagged.sentences])

finished = []
unfinished = []

for sentence in full_tokenized.sentences:
    try:
        if sentence.sent_id in retagged_ids:
            finished.append(sentence)
        else:
            int(sentence.sent_id)
            unfinished.append(sentence)
    except ValueError:
        finished.append(sentence)

full_tokenized.sentences = finished
CoNLL.write_doc2conll(full_tokenized, "sd_batch_2_1000.finished.conllu")

full_tokenized.sentences = unfinished
CoNLL.write_doc2conll(full_tokenized, "sd_batch_2_1000.unfinished.conllu")

