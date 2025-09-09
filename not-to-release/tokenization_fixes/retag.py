import argparse

import stanza
from stanza.utils.conll import CoNLL

parser = argparse.ArgumentParser(description='Retag a file')
parser.add_argument('input_filename', type=str, help='Which file to retag')
parser.add_argument('output_filename', type=str, help='Where to write the file')
args = parser.parse_args()


pipe = stanza.Pipeline("sd", package="default_accurate", processors="tokenize,pos", tokenize_pretokenized=True)
doc = CoNLL.conll2doc(args.input_filename)
doc2 = pipe(doc)
CoNLL.write_doc2conll(doc2, args.output_filename)

