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

    noxpos_doc = read_directory("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/dependencies/*")
    xpos_doc = read_directory("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/xpos_features/*",
                              "extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/xpos_standard/xpos_tagged_with_features.conllu", strip_xpos=False)

    print("%d sentences with no xpos or features" % len(noxpos_doc.sentences))
    print("%d sentences with xpos and features" % len(xpos_doc.sentences))

    noxpos_doc = filter_duplicates(noxpos_doc, xpos_doc)

    # read one specific doc with the intention of training on it exactly,
    # so we keep the UPOS close to the original
    filter_doc = read_directory("extern_data/ud2/git/UD_Sindhi-Isra/not-to-release/dependencies/sd_batch_4.800.conllu")
    noxpos_doc = filter_duplicates(noxpos_doc, filter_doc)

    train, dev, test = random_split(xpos_doc, weights=(0.8, 0.1, 0.1))
    print("Split the xpos doc into %d train, %d dev, %d test" % (len(train.sentences), len(dev.sentences), len(test.sentences)))
    #CoNLL.write_doc2conll(filtered_doc, "sd_isra_filtered.conllu")

    output_directory = "data/pos"
    shortname = "sd_isra"

    CoNLL.write_doc2conll(dev, os.path.join(output_directory, "%s.dev.in.conllu" % shortname))
    CoNLL.write_doc2conll(test, os.path.join(output_directory, "%s.test.in.conllu" % shortname))
    # TODO: write to the zip file
    with zipfile.ZipFile(os.path.join(output_directory, "%s.train.in.zip" % shortname), "w") as zout:
        with zout.open("sd_isra_train.in.conllu", mode='w') as fout:
            with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                CoNLL.write_doc2conll(train, tout)
        with zout.open("sd_isra_noxpos.conllu", mode='w') as fout:
            with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                CoNLL.write_doc2conll(noxpos_doc, tout)
        with zout.open("sd_batch_4.800.conllu", mode='w') as fout:
            with io.TextIOWrapper(fout, encoding="utf-8") as tout:
                CoNLL.write_doc2conll(filter_doc, tout)

if __name__ == '__main__':
    main()
