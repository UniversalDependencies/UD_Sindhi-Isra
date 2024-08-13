from stanza.utils.conll import CoNLL
from validate import validate

new_doc = CoNLL.conll2doc("sd_isra.leftover_output_jul_14_2024")
orig_doc = CoNLL.conll2doc("sd_isra.leftover.conllu")

for new_sent, orig_sent in zip(new_doc.sentences, orig_doc.sentences):
  new_sent.sent_id = orig_sent.sent_id

problem_sentences = validate(new_doc)


for sent_idx, (new_sent, orig_sent) in enumerate(zip(new_doc.sentences, orig_doc.sentences)):
  if sent_idx in problem_sentences:
    continue

  for new_word, orig_word in zip(new_sent.words, orig_sent.words):
    if orig_word.upos != new_word.upos:
      orig_word.upos = new_word.upos
      orig_word.xpos = None
      orig_word.feats = None
    orig_word.head = new_word.head
    orig_word.deprel = new_word.deprel

CoNLL.write_doc2conll(orig_doc, "sd_isra.leftover.conllu")
