"""
Convert a Sindhi dependency tree to Latex
"""

import argparse
import sys

from stanza.utils.conll import CoNLL

sys.stdout.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser(description='Convert the first dependency tree in this file to a Latex format')
parser.add_argument('filename', help='File to convert')
parser.add_argument('--separation', default='0.25cm', help='How wide apart to make the nodes')
parser.add_argument('--label', help='Label to add to the graph')
parser.add_argument('--caption', help='Caption to add to the graph')
parser.add_argument('--heads', default='', help='Which heads to include as arcs')
args = parser.parse_args()

doc = CoNLL.conll2doc(args.filename)
sentence = doc.sentences[0]

print("{:C}".format(sentence))

words = sentence.words
if words[-1].pos == 'PUNCT':
    words = words[:-1]

print(r"""
\begin{figure*}
\begin{center}
\begin{dependency}
  \begin{deptext}[column sep=%s]""" % args.separation)

converted_text = ["{\\sindhifont %s}" % word.text for word in reversed(words)]
for chunk in range(0, len(converted_text), 3):
    if chunk + 3 >= len(converted_text):
        ending = " \\\\"
    else:
        ending = " \\&"
    print("    %s%s" % (" \\& ".join(converted_text[chunk:chunk+3]), ending))

print(r"  \end{deptext}")

heads = map(int, args.heads.split(","))
for head in heads:
    target = len(words) + 1 - head
    if words[head-1].head == 0:
        print("""  \\deproot[edge style={blue!60!black,ultra thick},
           label style={fill=green!60,font=\\bfseries,text=black}]{%d}{root}""" % target)
    else:
        deprel = words[head-1].deprel
        source = words[head-1].head
        source = len(words) + 1 - source
        print("""  \\depedge[edge height=3ex,
           edge style={blue!60!black,ultra thick},
           label style={fill=green!60,font=\\bfseries,text=black}]{%d}{%d}{%s}""" % (source, target, deprel))


print(r"""\end{dependency}
\end{center}""")

if args.caption:
    print("\\caption{%s}" % args.caption)

if args.label:
    print("\\label{%s}" % args.label)

print(r"\end{figure*}")
