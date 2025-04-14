"""
Given a tsv of predicted lemmas and a tsv of corrected lemmas,
report how many were correct and how many should have been the
identity lemma.

Useful for paper writing about how well the lemma prediction is working
"""

fixed_filename = "../lemmas/predicted_lemmas_b1_corrected.tsv"
orig_filename = "../lemmas/original/predicted_lemmas_b1.tsv"

with open(fixed_filename) as fin:
    fixed_lines = fin.readlines()
    fixed_lines = [x.strip() for x in fixed_lines[1:]]
    fixed_lines = [x for x in fixed_lines if x]

with open(orig_filename) as fin:
    orig_lines = fin.readlines()
    orig_lines = [x.strip() for x in orig_lines[1:]]
    orig_lines = [x for x in orig_lines if x]

assert len(orig_lines) == len(fixed_lines)

total = 0
correct = 0
identity = 0
correct_identity = 0

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
        correct_identity += 1

print("%d predicted correct out of %d" % (correct, total))
print("%d identity out of %d" % (identity, total))
print("%d correct identity predictions" % correct_identity)
