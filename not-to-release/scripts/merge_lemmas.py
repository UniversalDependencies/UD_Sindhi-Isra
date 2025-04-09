import argparse
import glob
import sys

from stanza.utils.conll import CoNLL

def get_filenames():
    filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt") + ["../xpos_standard/xpos_tagged_with_features.conllu"]
    filenames.extend(glob.glob("../dependencies/*conllu"))
    return filenames

def read_tsv_files(tsv_files):
    lemmas = {}
    for filename in tsv_files:
        with open(filename, encoding="utf-8") as fin:
            lines = fin.readlines()
        lines = lines[1:]
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            pieces = line.split("\t")
            if len(pieces) < 3:
                raise ValueError("unexpected line format at %s line %d: only %d tab pieces" % (filename, line_idx+1))
            pieces = pieces[:3]
            # the lemma files should all be in the format word,upos,lemma
            lemmas[(pieces[0], pieces[1])] = pieces[2]
    return lemmas

def set_lemmas(filename, lemmas):
    print("Lemmatizing %s" % filename)
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            if (word.text, word.upos) in lemmas:
                word.lemma = lemmas[(word.text, word.upos)]
    CoNLL.write_doc2conll(doc, filename)


def main():
    tsv_files = glob.glob("../lemmas/*.tsv")
    lemmas = read_tsv_files(tsv_files)

    filenames = get_filenames()

    for filename in filenames:
        set_lemmas(filename, lemmas)

if __name__ == '__main__':
    main()
