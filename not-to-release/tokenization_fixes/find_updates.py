import argparse
import difflib

from stanza.utils.conll import CoNLL
from stanza import Pipeline

def yield_update_spans(orig_lines, new_lines):
    orig_idx = 0
    new_idx = 0

    while orig_idx < len(orig_lines):
        if new_lines[new_idx] == orig_lines[orig_idx]:
            yield orig_lines[orig_idx], new_lines[new_idx:new_idx+1]
            orig_idx += 1
            new_idx += 1
            continue
        matcher = difflib.SequenceMatcher(a=orig_lines[orig_idx], b=new_lines[new_idx])
        if len(matcher.get_opcodes()) == 3:
            operations = [x for x in matcher.get_opcodes() if x[0] != 'equal']
            if len(operations) == 1 and operations[0][2] - operations[0][1] < 5 and operations[0][4] - operations[0][3] < 5:
                yield orig_lines[orig_idx], new_lines[new_idx:new_idx+1]
                orig_idx += 1
                new_idx += 1
                continue
        if orig_idx == 190 and new_idx == 265:
            # difflib seems to be going haywire here, so manually skip it
            yield orig_lines[orig_idx], new_lines[new_idx:new_idx+2]
            orig_idx += 1
            new_idx += 2
            continue
        for num_chunks in range(2, 8):
            orig_line = orig_lines[orig_idx].replace(" ", "").replace(".", "")
            new_line = "".join(new_lines[new_idx:new_idx+num_chunks]).replace(" ", "").replace(".", "")
            if orig_line == new_line:
                yield orig_lines[orig_idx], new_lines[new_idx:new_idx+num_chunks]
                orig_idx += 1
                new_idx += num_chunks
                break
            new_line = "".join(new_lines[new_idx:new_idx+num_chunks])
            matcher = difflib.SequenceMatcher(a=orig_lines[orig_idx], b=new_line)
            # expected / acceptable: equal text with a period, for example
            if len(matcher.get_opcodes()) > num_chunks * 2 + 1:
                continue
            operations = [x for x in matcher.get_opcodes() if x[0] != 'equal']
            if len(operations) > num_chunks:
                continue
            if any(op[4] - op[3] > 5 or op[2] - op[1] > 5 for op in operations):
                continue
            orig_idx += 1
            new_idx += num_chunks
            yield orig_lines[orig_idx], new_lines[new_idx:new_idx+num_chunks]
            break
        else:
            print("Could not figure out: %d %d" % (orig_idx, new_idx))
            print(orig_lines[orig_idx])
            print(new_lines[new_idx])
            for num_chunks in range(2, 8):
                new_line = "".join(new_lines[new_idx:new_idx+num_chunks])
                print(orig_lines[orig_idx])
                print(new_line)

                matcher = difflib.SequenceMatcher(a=orig_lines[orig_idx], b="".join(new_lines[new_idx:new_idx+num_chunks]))
                operations = [x for x in matcher.get_opcodes() if x[0] != 'equal']
                print(len(matcher.get_opcodes()), num_chunks * 2 + 1, len(matcher.get_opcodes()) > num_chunks * 2 + 1)
                print(len(operations) > num_chunks)
                print(any(op[4] - op[3] > 5 or op[2] - op[1] > 5 for op in operations))
                print(operations)
            break

def main():
    parser = argparse.ArgumentParser(description='Find tokenization edits relative to a particular conllu file and reparse those sentences')
    parser.add_argument('filename', type=str, help='File to validate')
    args = parser.parse_args()

    with open("two_nsubj.txt") as fin:
        orig_lines = fin.readlines()
        orig_lines = [x.strip() for x in orig_lines]

    with open("two_nsubj_rawtextreviewed.txt") as fin:
        new_lines = fin.readlines()
        new_lines = [x.strip() for x in new_lines]

    unchanged = sum(x in orig_lines for x in new_lines)
    print("%d lines unchanged" % unchanged)

    print("%d lines in original" % len(orig_lines))
    print("%d lines in new" % len(new_lines))

    doc = CoNLL.conll2doc(args.filename)
    known_text = {sent.text.replace(" ", "") for sent in doc.sentences}

    pipe = Pipeline("sd", processors="tokenize,pos,lemma,depparse", package="default_accurate", tokenize_no_ssplit=True)

    docs = []

    errors = 0
    for span in yield_update_spans(orig_lines, new_lines):
        if span[0].replace(" ", "") in known_text:
            if len(span[1]) > 1 or span[0] != span[1][0]:
                if len(span[1]) == 1 and span[0][-1] in (".", "،", "؟") and span[0][-2] == ' ' and span[1][0][-1] == span[0][-1] and span[0][:-2] == span[1][0][:-1]:
                    continue
                errors += 1
                print("Replacing:")
                print("  |%s|" % span[0])
                print("with")
                for sentence in span[1]:
                    print("  |%s|" % sentence)
                    # not efficient... not too many sentences, fortunately
                    doc = pipe(sentence)
                    assert len(doc.sentences) == 1
                    doc.sentences[0].add_comment("# orig_text = %s" % span[0])
                    for token in doc.sentences[0].tokens:
                        token._start_char = None
                        token._end_char = None
                    for word in doc.sentences[0].words:
                        word._start_char = None
                        word._end_char = None
                    doc.sentences[0].sent_id = str(len(docs)+1)
                    docs.append(doc)
            #if len(span[1]) == 1 and span[0] != span[1][0]:
            #    print(span[0])
            #    print(span[1][0])

    print(errors)
    for doc in docs:
        CoNLL.write_doc2conll(doc, "twonsubj_reparsed.conllu", mode='a')

if __name__ == '__main__':
    main()

