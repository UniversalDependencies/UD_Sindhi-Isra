# A script to check the Voice= attributes on VERBs
# could have done AUXs as well, actually

import argparse
import glob
import sys

from collections import Counter

from stanza.utils.conll import CoNLL

def get_filenames():
    filenames = glob.glob("../xpos_features/*conllu") + glob.glob("../xpos_features/*txt")
    return filenames

def main():
    voice_act = Counter()
    voice_pass = Counter()
    no_voice = Counter()

    filenames = get_filenames()
    for filename in filenames:
        doc = CoNLL.conll2doc(filename)
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.upos == "VERB":
                    if not word.feats:
                        no_voice[word.text] += 1
                        continue

                    pieces = word.feats.split("|")
                    for piece in pieces:
                        if piece.startswith("Voice="):
                            break
                    else:
                        no_voice[word.text] += 1
                        continue
                    if piece == "Voice=Pass":
                        voice_pass[word.text] += 1
                    elif piece == "Voice=Act":
                        voice_act[word.text] += 1
                    else:
                        raise ValueError("Unknown Voice: %s" % piece)

    with open("conflict.tsv", "w") as fout:
        for verb in voice_pass:
            if verb in voice_act:
                fout.write("%s\t%d\t%d\t%d\n" % (verb, voice_pass[verb], voice_act[verb], no_voice[verb]))

    with open("passive_only.tsv", "w") as fout:
        for verb in voice_pass:
            if verb not in voice_act:
                fout.write("%s\t%d\t%d\t%d\n" % (verb, voice_pass[verb], voice_act[verb], no_voice[verb]))

    with open("active_only.tsv", "w") as fout:
        for verb in voice_act:
            if verb not in voice_pass:
                fout.write("%s\t%d\t%d\t%d\n" % (verb, voice_pass[verb], voice_act[verb], no_voice[verb]))

if __name__ == '__main__':
    main()
