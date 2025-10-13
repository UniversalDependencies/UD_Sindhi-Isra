# A very basic script to go through an archive of Sindhi Adabi looking for possible text matches

import glob
import os

from stanza.utils.conll import CoNLL

raw_text_filename = "/home/john/extern_data/sindhi/sindhiadabi/extracted_sindhiadabi.txt"
with open(raw_text_filename) as fin:
    raw_text = fin.read()

filename = "../xpos_features/sd_780_combined.conllu"
#filename = "../xpos_features/sd_batch_5_600.conllu"
doc = CoNLL.conll2doc(filename)

for sentence in doc.sentences:
    if sentence.text in raw_text:
        print(sentence.sent_id)
        print(sentence.text)
        continue
    for endpoint in range(4, len(sentence.words)):
        text = " ".join([x.text for x in sentence.words[endpoint-4:endpoint]])
        if text in raw_text:
            print(sentence.sent_id)
            print(text)
            print(sentence.text)
            break
