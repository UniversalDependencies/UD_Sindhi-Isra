"""
Given a tsv of predicted lemmas and a tsv of corrected lemmas,
report how many were correct and how many should have been the
identity lemma.

Useful for paper writing about how well the lemma prediction is working
"""

import argparse

parser = argparse.ArgumentParser(description='Count how many correct predictions are in a lemmatization file')
parser.add_argument('--original', default="../lemmas/original/predicted_lemmas_b2.tsv", help='File of original predictions')
parser.add_argument('--fixed',    default="../lemmas/predicted_lemmas_b2_corrected.tsv", help='File of gold updates')
args = parser.parse_args()

with open(args.fixed) as fin:
    fixed_lines = fin.readlines()
    fixed_lines = [x.strip() for x in fixed_lines[1:]]
    fixed_lines = [x for x in fixed_lines if x]

with open(args.original) as fin:
    orig_lines = fin.readlines()
    orig_lines = [x.strip() for x in orig_lines[1:]]
    orig_lines = [x for x in orig_lines if x]

assert len(orig_lines) == len(fixed_lines)

total = 0
correct = 0
identity = 0
correct_predicted_identity = 0
predicted_identity = 0

for fl, ol in zip(fixed_lines, orig_lines):
    fixed_pieces = fl.split("\t")
    orig_pieces = ol.split("\t")
    if len(fixed_pieces) > 3:
        continue
    total += 1
    if fixed_pieces[2] == orig_pieces[2]:
        correct += 1
    if fixed_pieces[0] == fixed_pieces[2]:
        identity += 1
    if fixed_pieces[2] == orig_pieces[2] and fixed_pieces[0] == fixed_pieces[2]:
        correct_predicted_identity += 1
    if orig_pieces[0] == orig_pieces[2]:
        predicted_identity += 1

print("%d predicted correct out of %d" % (correct, total))
print("%d identity out of %d" % (identity, total))
print("%d identity predictions" % predicted_identity)
print("%d correct identity predictions" % correct_predicted_identity)

