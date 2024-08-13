import glob
import sys

from stanza.utils.conll import CoNLL

def merge_edits(new_doc):
    sentences = {}
    for sentence in new_doc.sentences:
        if not sentence.text:
            raise ValueError("Sentence %s has no text!" % sentence.sent_id)
        text = sentence.text.replace(" ", "")
        if sentence in sentences:
            raise ValueError("Multiple copies of sentence found: %s = %s" % (sentence.sent_id, sentence.text))
        sentences[text] = sentence

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
    new_doc = CoNLL.conll2doc(sys.argv[1])
    merge_edits(new_doc)

if __name__ == '__main__':
    main()
