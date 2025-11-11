# This script helped search for and assign sent_ids to the sentences
# in our dataset which matched text from the MD dataset

import glob
import os

from stanza.utils.conll import CoNLL

known_text = {}
duplicates = 0

tokenization_doc = CoNLL.conll2doc("../../../UD_Sindhi-MazharDootio/sd_mazhardootio-ud-test.conllu")
for sentence in tokenization_doc.sentences:
    text = sentence.text.replace(" ", "")
    if sentence.sent_id == '662':
        print(text)
    if text not in known_text:
        known_text[text] = sentence.sent_id
    else:
        duplicates += 1
print("The MD dataset had %d duplicates" % duplicates)

def relabel(filename, known_text, found_text):
    doc = CoNLL.conll2doc(filename)
    count = 0
    for sentence in doc.sentences:
        text = sentence.text.replace(" ", "")
        if sentence.sent_id == '662':
            print(text)
        if text in known_text:
            count += 1
            if not sentence.sent_id.startswith("MD-"):
                sentence.sent_id = "MD-%s" % known_text[text]
            if found_text is not None:
                found_text.add(text)
    CoNLL.write_doc2conll(doc, filename)
    print("  Total from %s: %d / %d" % (filename, count, len(doc.sentences)))

found_text = set()
    
filenames = glob.glob("../dependencies/*")
#filenames = [x for x in filenames if os.path.split(x)[1] not in outside_filenames]
for filename in filenames:
    relabel(filename, known_text, found_text)

for text in known_text:
    if text not in found_text:
        print(known_text[text])

filenames = glob.glob("../xpos_features/*")
for filename in filenames:
    relabel(filename, known_text, None)
