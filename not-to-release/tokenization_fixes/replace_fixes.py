"""
Replace fix tokenization sentences in the tokenization dataset and the dependencies dataset
"""

import argparse
from collections import defaultdict

from stanza.utils.conll import CoNLL

def replace_sentences(sentences, orig_to_new, reindex=True):
    new_sentences = []
    for sentence in sentences:
        if sentence.text in orig_to_new:
            if reindex:
                sent_id = sentence.sent_id
                for idx, new_sent in enumerate(orig_to_new[sentence.text]):
                    new_sent_id = sent_id + chr(97 + idx)
                    new_sent.sent_id = new_sent_id
            new_sentences.extend(orig_to_new[sentence.text])
        else:
            new_sentences.append(sentence)
    return new_sentences

parser = argparse.ArgumentParser(description='Replace some retokenized & reparsed sentences')
parser.add_argument('--reparsed', default="../xpos_features/sd_batch_3_retok.conllu")
parser.add_argument('--original', default=["../dependencies/sd_batch_3.conllu"], nargs="+")
args = parser.parse_args()
tokenized_filename = "../tokenization/combined_tokenization.conllu"

reparsed = CoNLL.conll2doc(args.reparsed)
full_tokenized = CoNLL.conll2doc(tokenized_filename)

orig_to_new = defaultdict(list)

for sentence in reparsed.sentences:
    comments = sentence.comments
    for comment in comments:
        if comment.startswith("# orig_text"):
            orig_text = comment.split("=")[1].strip()
            break
    else:
        raise ValueError("Missing orig_text on a sentence")
    comments = [x for x in comments if not x.startswith("# orig_text")]
    sentence._comments = comments
    orig_to_new[orig_text].append(sentence)

full_tokenized.sentences = replace_sentences(full_tokenized.sentences, orig_to_new)
CoNLL.write_doc2conll(full_tokenized, tokenized_filename)

for filename in args.original:
    original = CoNLL.conll2doc(filename)
    original.sentences = replace_sentences(original.sentences, orig_to_new, reindex=False)
    CoNLL.write_doc2conll(original, filename)
