import argparse
import glob
import io
import os
import random
import zipfile

from stanza.models.common.doc import Document
from stanza.utils.conll import CoNLL
from stanza.utils.datasets.random_split_conllu import random_split

def read_directory(*globs, strip_xpos=True):
    sentences = []
    comments = []

    for glob_path in globs:
        raw_files = glob.glob(glob_path)
        for filename in raw_files:
            doc = CoNLL.conll2doc(filename)

            for sent in doc.sentences:
                if strip_xpos:
                    for word in sent.words:
                        word.feats = None
                        word.xpos = None
                sentences.append(sent.to_dict())
                comments.append(sent.comments)
    doc = Document(sentences, comments=comments)
    return doc

def filter_duplicates(orig_doc, filter_doc):
    filter_text = {sent.text.replace(" ", "") for sent in filter_doc.sentences}

    filtered_sentences = []
    filtered_comments = []

    for sent in orig_doc.sentences:
        if sent.text.replace(" ", "") in filter_text:
            continue
        filtered_sentences.append(sent.to_dict())
        filtered_comments.append(sent.comments)

    filtered_doc = Document(filtered_sentences, comments=filtered_comments)

    return filtered_doc

def main():
    random.seed(1234)
    parser = argparse.ArgumentParser(description='Build a combined training document for a Sindhi tagger')
    parser.add_argument('--mode', default='pos', choices=['pos', 'depparse'], help='Build a pos dataset or a depparse dataset')
    parser.add_argument('--retagged', default="extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/dependencies/sd_batch_3.conllu", help='File to retag')
    parser.add_argument('--no_retagged', dest='retagged', action='store_const', const=None, help="Don't retag anything")
    parser.add_argument('--raw_retagged', default="sd_batch_3.conllu", help="Somewhere to write the filtered retag file")
    args = parser.parse_args()

    noxpos_doc = read_directory("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/dependencies/*")
    xpos_doc = read_directory("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/xpos_features/*",
                              "extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/xpos_standard/xpos_tagged_with_features.conllu", strip_xpos=False)

    print("%d sentences with xpos and features" % len(xpos_doc.sentences))
    print("%d sentences with no xpos or features" % len(noxpos_doc.sentences))

    noxpos_doc = filter_duplicates(noxpos_doc, xpos_doc)
    print("%d sentences with no xpos or features after filtering duplicates" % len(noxpos_doc.sentences))

    shortname = "sd_isra"

    if args.mode == 'pos':
        # read one specific doc with the intention of training on it exactly,
        # so we keep the UPOS close to the original
        if args.retagged:
            filter_doc = read_directory(args.retagged)
            print("Doc to be tagged, before filtering: %d sentences" % len(filter_doc.sentences))
            filter_doc = filter_duplicates(filter_doc, xpos_doc)
            print("Doc to be tagged, after filtering: %d sentences" % len(filter_doc.sentences))
            noxpos_doc = filter_duplicates(noxpos_doc, filter_doc)

        train, dev, test = random_split(xpos_doc, weights=(0.8, 0.1, 0.1))
        print("Split the xpos doc into %d train, %d dev, %d test" % (len(train.sentences), len(dev.sentences), len(test.sentences)))

        output_directory = "data/pos"

        if args.retagged and args.raw_retagged:
            CoNLL.write_doc2conll(filter_doc, args.raw_retagged)
        CoNLL.write_doc2conll(dev, os.path.join(output_directory, "%s.dev.in.conllu" % shortname))
        CoNLL.write_doc2conll(test, os.path.join(output_directory, "%s.test.in.conllu" % shortname))
        with zipfile.ZipFile(os.path.join(output_directory, "%s.train.in.zip" % shortname), "w") as zout:
            with zout.open("sd_isra_train.in.conllu", mode='w') as fout:
                with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                    CoNLL.write_doc2conll(train, tout)
            with zout.open("sd_isra_noxpos.conllu", mode='w') as fout:
                with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                    CoNLL.write_doc2conll(noxpos_doc, tout)
            if args.retagged:
                retagged_filename = os.path.split(retagged)[1]
                with zout.open(retagged_filename, mode='w') as fout:
                    with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                        CoNLL.write_doc2conll(filter_doc, tout)
    elif args.mode == 'depparse':
        sentences = xpos_doc.sentences + noxpos_doc.sentences
        xpos_doc.sentences = sentences
        print("%d total training sentences" % len(xpos_doc.sentences))

        train, dev, test = random_split(xpos_doc, weights=(0.8, 0.1, 0.1))
        print("Split the combined doc into %d train, %d dev, %d test" % (len(train.sentences), len(dev.sentences), len(test.sentences)))

        output_directory = "data/depparse"
        CoNLL.write_doc2conll(train, os.path.join(output_directory, "%s.train.in.conllu" % shortname))
        CoNLL.write_doc2conll(dev, os.path.join(output_directory, "%s.dev.in.conllu" % shortname))
        CoNLL.write_doc2conll(test, os.path.join(output_directory, "%s.test.in.conllu" % shortname))

if __name__ == '__main__':
    main()
