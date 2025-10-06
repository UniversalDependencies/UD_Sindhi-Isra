import argparse
import glob

from stanza.utils.conll import CoNLL

parser = argparse.ArgumentParser(description='Look for sentences which have not yet been xpos-featurized')
parser.add_argument('--ignore_split', action='store_true', default=False, dest='ignore_split',
                    help='Ignore the sentences which are apparently already resplit, such as with a letter at the end of the sent_id')
parser.add_argument('--upos_file', default='../dependencies/sd_bad_tokenization.conllu')
# previously would do: "../xpos_features/sd_batch_2*"
parser.add_argument('--xpos_glob', default="../xpos_features/*")
args = parser.parse_args()

full_tokenized = CoNLL.conll2doc(args.upos_file)
retagged_ids = set()

for filename in glob.glob(args.xpos_glob):
    already_tagged = CoNLL.conll2doc(filename)
    retagged_ids = retagged_ids.union([sent.sent_id for sent in already_tagged.sentences])

finished = []
unfinished = []

print("Found %d sentences already retagged" % len(retagged_ids))

for sentence in full_tokenized.sentences:
    try:
        if sentence.sent_id in retagged_ids:
            finished.append(sentence)
        else:
            if args.ignore_split:
                int(sentence.sent_id)
            unfinished.append(sentence)
    except ValueError:
        finished.append(sentence)

full_tokenized.sentences = finished
CoNLL.write_doc2conll(full_tokenized, "sd_nopos_1000.finished.conllu")

print("Writing %d unfinished sentences" % len(unfinished))
full_tokenized.sentences = unfinished
CoNLL.write_doc2conll(full_tokenized, "sd_nopos_1000.unfinished.conllu")

