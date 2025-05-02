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
    locations = {}
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
            if len(pieces) > 3:
                # this was a lemma with a note on it, such as a wrong tag or wrong tokenization
                continue
            pieces = pieces[:3]
            word_tag = (pieces[0], pieces[1])
            # the lemma files should all be in the format word,upos,lemma
            if lemmas.get((pieces[0], pieces[1]), pieces[2]) != pieces[2]:
                raise ValueError("Found a conflict: word |%s| POS %s  Originally |%s| at %s  Now |%s| at %s" % (pieces[0], pieces[1], lemmas[word_tag], locations[word_tag], pieces[2], (filename, line_idx)))
            lemmas[word_tag] = pieces[2]
            locations[word_tag] = (filename, line_idx)
    return lemmas

def set_lemmas(filename, lemmas, remove_existing):
    print("Lemmatizing %s" % filename)
    doc = CoNLL.conll2doc(filename)
    for sentence in doc.sentences:
        for word in sentence.words:
            if (word.text, word.upos) in lemmas:
                word.lemma = lemmas[(word.text, word.upos)]
            elif remove_existing:
                word.lemma = None
    CoNLL.write_doc2conll(doc, filename)


def main():
    parser = argparse.ArgumentParser(description='Merge all known lemmas into the conllu files')
    parser.add_argument('--remove_existing', action='store_true', default=False, dest='remove_existing',
                        help="If a lemma is currently set, but is not in the known lemma files, remove it")
    args = parser.parse_args()

    tsv_files = glob.glob("../lemmas/*.tsv")
    lemmas = read_tsv_files(tsv_files)

    filenames = get_filenames()

    for filename in filenames:
        set_lemmas(filename, lemmas, args.remove_existing)

if __name__ == '__main__':
    main()
