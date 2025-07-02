import argparse


from stanza import Pipeline
from stanza.utils.conll import CoNLL

parser = argparse.ArgumentParser(description='Reparse some sentences into a conllu file')
parser.add_argument('--use_local_models', default=False, action='store_true', help="Use models from the saved_models dirs")
args = parser.parse_args()

pipeline_args = {
    "processors":         "tokenize,pos,lemma,depparse",
    "package":            "default_accurate",
    "tokenize_no_spplit": True,
}

if args.use_local_models:
    pipeline_args["depparse_model_path"] = "saved_models/depparse/sd_isra_muril-large-cased_parser.pt"
    pipeline_args["pos_model_path"] = "saved_models/pos/sd_isra_muril-large-cased_tagger.pt"

pipe = Pipeline("sd", **pipeline_args)

with open("resplit_sentences.txt") as fin:
#with open("missing_md.2.txt") as fin:
#with open("sd_batch_3_reparse.txt") as fin:
    lines = fin.readlines()
    lines = [x.strip() for x in lines]
    lines = [x for x in lines if x]

docs = [pipe(x) for x in lines]
for doc in docs:
    assert len(doc.sentences) == 1
    for token in doc.sentences[0].tokens:
        token._start_char = None
        token._end_char = None
    for word in doc.sentences[0].words:
        word._start_char = None
        word._end_char = None
        word._lemma = None

for doc in docs:
    CoNLL.write_doc2conll(doc, "resplit.conllu", mode='a')
    #CoNLL.write_doc2conll(doc, "missing_md.2.conllu", mode='a')
    #CoNLL.write_doc2conll(doc, "sd_batch_3_reparse.conllu", mode='a')

