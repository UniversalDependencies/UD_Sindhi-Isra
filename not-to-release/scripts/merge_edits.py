import argparse
import glob
import sys

from stanza.utils.conll import CoNLL

def merge_edits(new_doc, merge_xpos=False):
    sentences = {}
    for sentence in new_doc.sentences:
        if not sentence.text:
            raise ValueError("Sentence %s has no text!" % sentence.sent_id)
        text = sentence.text.replace(" ", "")
        if sentence in sentences:
            raise ValueError("Multiple copies of sentence found: %s = %s" % (sentence.sent_id, sentence.text))
        sentences[text] = sentence

    if merge_xpos:
        filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt")
    else:
        filenames = glob.glob("../dependencies/*conllu")
    for filename in filenames:
        print(filename)

        orig_doc = CoNLL.conll2doc(filename)
        new_sentences = []
        edited = False
        for sentence in orig_doc.sentences:
            if not sentence.text:
                raise ValueError("Sentence %s in %s has no text!" % (sentence.sent_id, filename))
            text = sentence.text.replace(" ", "")
            if text in sentences:
                new_sentences.append(sentences[text])
                if sentence.sent_id:
                    new_sentences[-1].sent_id = sentence.sent_id
                del sentences[text]
                edited = True
            else:
                new_sentences.append(sentence)
        if edited:
            orig_doc.sentences = new_sentences
            CoNLL.write_doc2conll(orig_doc, filename)


    if len(sentences) > 0:
        print("Unknown sentences: %d" % len(sentences))
        for sentence in list(sentences.values())[:5]:
            print("{:C}".format(sentence))
            print()
    else:
        print("All sentences accounted for!")

def main():
    parser = argparse.ArgumentParser(description='Validate a file of SD dependencies & tags')
    parser.add_argument('filename', help='File to merge')
    parser.add_argument('--merge_deps', action='store_false', default=True, dest='merge_xpos',
                        help="Merge into the dependencies directory instead of the xpos directory")
    parser.add_argument('--merge_xpos', action='store_true', dest='merge_xpos',
                        help="Merge into the xpos directory instead of the dependencies directory")
    args = parser.parse_args()

    new_doc = CoNLL.conll2doc(args.filename)
    for sentence in new_doc.sentences:
        # remove some comments which are in the document's sentences
        # as artifacts from the search / hints from the search
        sentence.comments.remove("highlight deprels")
        sentence.comments.remove("highlight tokens")
        semgrex = [comment for comment in sentence.comments if comment.startswith("# semgrex")]
        for comment in semgrex:
            sentence.comments.remove(comment)
    merge_edits(new_doc, merge_xpos=args.merge_xpos)

if __name__ == '__main__':
    main()
