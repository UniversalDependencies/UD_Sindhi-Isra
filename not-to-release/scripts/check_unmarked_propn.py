import argparse
import glob
import os

from stanza.utils.conll import CoNLL
from stanza.utils.default_paths import get_default_paths

def read_dependency_docs():
    paths = get_default_paths()
    dependency_glob = os.path.join(paths["UDBASE_GIT"], "UD_Sindhi-Isra/not-to-release/dependencies/*")
    filenames = glob.glob(dependency_glob)

    print("Reading sentences from %d files in %s" % (len(filenames), dependency_glob))
    sentences = {}
    for filename in filenames:
        doc = CoNLL.conll2doc(filename, keep_line_numbers=True)
        for sentence in doc.sentences:
            sentences[sentence.text] = sentence
    print("Read %d sentences" % len(sentences))
    return sentences

def check_proper_names(filename, orig_sentences):
    doc = CoNLL.conll2doc(filename, keep_line_numbers=True)
    for sentence in doc.sentences:
        found = False
        orig_sentence = orig_sentences.get(sentence.text)
        if orig_sentence is None:
            print("Could not find sentence: |%s|" % sentence.text)
            continue
        for cur_word, orig_word in zip(sentence.words, orig_sentence.words):
            if cur_word.pos == 'NOUN' and orig_word.pos == 'PROPN':
                found = True
                break
        if found:
            print("Found a difference in filename %s sentence %s" % (filename, sentence.sent_id))
            print("|%s|" % sentence.text)
            for cur_word, orig_word in zip(sentence.words, orig_sentence.words):
                if cur_word.pos == 'NOUN' and orig_word.pos == 'PROPN':
                    print("|%s|\tcur: %s\torig: %s ***" % (cur_word.text, cur_word.pos, orig_word.pos))
                else:
                    print("|%s|\tcur: %s\torig: %s" % (cur_word.text, cur_word.pos, orig_word.pos))

                

def main():
    parser = argparse.ArgumentParser(description='Check for PROPN which were marked in .../dependencies but are now not marked in .../xpos_features')
    parser.add_argument('filename', nargs='+', help='File to check')
    args = parser.parse_args()

    orig_sentences = read_dependency_docs()

    for filename in args.filename:
        check_proper_names(filename, orig_sentences)

if __name__ == '__main__':
    main()

