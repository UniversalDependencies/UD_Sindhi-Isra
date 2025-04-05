import argparse
import glob
import io
import os
import random
import zipfile

from stanza.models.common.doc import Document
from stanza.utils.conll import CoNLL
from stanza.utils.default_paths import get_default_paths
from stanza.utils.datasets.random_split_conllu import random_split

def remove_xpos_and_features(doc):
    for sent in doc.sentences:
        for word in sent.words:
            word.feats = None
            word.xpos = None


def read_directory(*globs, strip_xpos=True):
    sentences = []
    comments = []

    for glob_path in globs:
        raw_files = glob.glob(glob_path)
        if len(raw_files) == 0:
            raise FileNotFoundError("Path %s requested but was empty!" % glob_path)
        for filename in raw_files:
            doc = CoNLL.conll2doc(filename)

            for sent in doc.sentences:
                sentences.append(sent.to_dict())
                comments.append(sent.comments)
    doc = Document(sentences, comments=comments)
    if strip_xpos:
        remove_xpos_and_features(doc)
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

def random_select(doc, size):
    """
    Return :size of the sentences from doc
    """
    sentences = doc.sentences
    random.seed(1234)
    random.shuffle(sentences)
    sentence_dicts = [sent.to_dict() for sent in sentences[:size]]
    sentence_comments = [sent.comments for sent in sentences[:size]]
    return Document(sentence_dicts, comments=sentence_comments)


def main():
    paths = get_default_paths()

    parser = argparse.ArgumentParser(description='Build a combined training document for a Sindhi tagger')
    parser.add_argument('--mode', default='pos', choices=['pos', 'upos', 'depparse'], help='Build a pos dataset, a UPOS only dataset, or a depparse dataset')
    #parser.add_argument('--retagged', default=os.path.join(paths["UDBASE_GIT"], "UD_Sindhi-Isra/not-to-release/dependencies/sd_batch_3.conllu"), help='File to retag')
    parser.add_argument('--retagged', default=None, help='File to retag')
    parser.add_argument('--no_retagged', dest='retagged', action='store_const', const=None, help="Don't retag anything")
    parser.add_argument('--raw_retagged', default="sd_batch_3.conllu", help="Somewhere to write the filtered retag file")

    parser.add_argument('--use_hindi', default=False, action='store_true', help="Include Hindi trees in the dataset")
    parser.add_argument('--use_marathi', default=False, action='store_true', help="Include Marathi trees in the dataset")
    parser.add_argument('--use_tamil', default=False, action='store_true', help="Include Tamil trees in the dataset")
    parser.add_argument('--use_urdu', default=False, action='store_true', help="Include Urdu trees in the dataset")

    parser.add_argument('--dataset_name', default='sd_isra', help='What name to use for the dataset')
    parser.add_argument('--sindhi_train_size', type=int, default=None, help='Only use this many Sindhi trees for train')
    parser.add_argument('--sindhi_dev_size', type=int, default=None, help='Only use this many Sindhi trees for dev')
    args = parser.parse_args()

    noxpos_doc = read_directory(os.path.join(paths["UDBASE_GIT"], "UD_Sindhi-Isra/not-to-release/dependencies/*"))
    xpos_doc = read_directory(os.path.join(paths["UDBASE_GIT"], "UD_Sindhi-Isra/not-to-release/xpos_features/*"),
                              os.path.join(paths["UDBASE_GIT"], "UD_Sindhi-Isra/not-to-release/xpos_standard/xpos_tagged_with_features.conllu"), strip_xpos=False)

    print("%d sentences with xpos and features" % len(xpos_doc.sentences))
    print("%d sentences with no xpos or features" % len(noxpos_doc.sentences))

    noxpos_doc = filter_duplicates(noxpos_doc, xpos_doc)
    print("%d sentences with no xpos or features after filtering duplicates" % len(noxpos_doc.sentences))

    extra_docs = {}
    if args.use_tamil:
        extra_docs['tamil'] = read_directory(os.path.join(paths["UDBASE"], "UD_Tamil-TTB/ta_ttb-ud-train.conllu"))
    if args.use_marathi:
        extra_docs['marathi'] = read_directory(os.path.join(paths["UDBASE"], "UD_Marathi-UFAL/mr_ufal-ud-train.conllu"))
    if args.use_hindi:
        hindi_doc = read_directory(os.path.join(paths["UDBASE"], "UD_Hindi-HDTB/hi_hdtb-ud-train.conllu"))
        hindi_doc = random_select(hindi_doc, 1000)
        extra_docs['hindi'] = hindi_doc
    if args.use_urdu:
        urdu_doc = read_directory(os.path.join(paths["UDBASE"], "UD_Urdu-UDTB/ur_udtb-ud-train.conllu"))
        urdu_doc = random_select(urdu_doc, 1000)
        extra_docs['urdu'] = urdu_doc

    if args.mode == 'pos':
        output_directory = "data/pos"

        # read one specific doc with the intention of training on it exactly,
        # so we keep the UPOS close to the original
        if args.retagged:
            filter_doc = read_directory(args.retagged)
            print("Doc to be tagged, before filtering: %d sentences" % len(filter_doc.sentences))
            filter_doc = filter_duplicates(filter_doc, xpos_doc)
            print("Doc to be tagged, after filtering: %d sentences" % len(filter_doc.sentences))
            noxpos_doc = filter_duplicates(noxpos_doc, filter_doc)

        random.seed(1234)
        train, dev, test = random_split(xpos_doc, weights=(0.8, 0.1, 0.1))
        print("Split the xpos doc into %d train, %d dev, %d test" % (len(train.sentences), len(dev.sentences), len(test.sentences)))

        if args.retagged and args.raw_retagged:
            CoNLL.write_doc2conll(filter_doc, args.raw_retagged)
        train_datasets = {
            "sd_isra_train.in.conllu": train,
            "sd_isra_noxpos.conllu":   noxpos_doc,
        }
        if args.retagged:
            train_datasets[os.path.split(args.retagged)[1]] = filter_doc
        for name in extra_docs:
            train_datasets["%s.conllu" % name] = extra_docs[name]

    elif args.mode == 'depparse' or args.mode == 'upos':
        sentences = xpos_doc.sentences + noxpos_doc.sentences
        xpos_doc.sentences = sentences
        print("%d total training sentences" % len(xpos_doc.sentences))

        if args.mode == 'upos':
            remove_xpos_and_features(xpos_doc)
            output_directory = paths["POS_DATA_DIR"]
        else:
            output_directory = paths["DEPPARSE_DATA_DIR"]

        random.seed(1234)
        train, dev, test = random_split(xpos_doc, weights=(0.8, 0.1, 0.1))
        print("Split the combined doc into %d train, %d dev, %d test" % (len(train.sentences), len(dev.sentences), len(test.sentences)))

        if args.sindhi_train_size is not None:
            train = random_select(train, args.sindhi_train_size)

        train_datasets = {
            "sd_isra_train.in.conllu": train
        }
        for name in extra_docs:
            train_datasets["%s.conllu" % name] = extra_docs[name]

    if args.sindhi_dev_size is not None:
        dev = random_select(dev, args.sindhi_dev_size)

    print("Writing to %s" % output_directory)
    shortname = args.dataset_name
    CoNLL.write_doc2conll(dev, os.path.join(output_directory, "%s.dev.in.conllu" % shortname))
    CoNLL.write_doc2conll(test, os.path.join(output_directory, "%s.test.in.conllu" % shortname))
    train_filename = os.path.join(output_directory, "%s.train.in.zip" % shortname)
    print("Writing training data to %s" % train_filename)
    with zipfile.ZipFile(train_filename, "w") as zout:
        for name in train_datasets:
            train_doc = train_datasets[name]
            if len(train_doc.sentences) == 0:
                continue
            with zout.open(name, mode='w') as fout:
                with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                    print("Writing %d sentences from %s to zipfile" % (len(train_doc.sentences), name))
                    CoNLL.write_doc2conll(train_doc, tout)

if __name__ == '__main__':
    main()
