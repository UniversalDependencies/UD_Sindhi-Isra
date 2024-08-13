from stanza.utils.conll import CoNLL

files = [
    "sd_isra_initial_gold_100.conllu",
    "Sindhi_50Sentences_Jan_17.conllu",
    "Sindhi_100sentences_Jan_17.conllu",
    "sindhi_300_deps.conllu",
    "sd_780.conllu",
    "sd_isra_relabled_100.conllu",
    "sd_small_update.conllu",
    "sd_1000_repeats.fixed.conllu",
    "sd_1000_repeats.fixed.p2.conllu",
    "sd_punct_batch.conllu",
    "sd_batch_2_1000.conllu",
    "sd_batch_3.conllu",
    "sd_nopos_1000.conllu",
    "sd_batch_4.800.conllu",
    "sd_batch_5_600.conllu",
]


known_text = set()
for filename in files:
    doc = CoNLL.conll2doc(filename)

    sentences = []
    for sentence in doc.sentences:
        if not sentence.text or not sentence.text.strip():
            print(filename, sentence.sent_id)
        text = sentence.text.strip()
        if text in known_text:
            continue
        known_text.add(text)
        sentences.append(sentence)
    print("Filename %s had %d sentences; %d were new" % (filename, len(doc.sentences), len(sentences)))
    doc.sentences = sentences
    CoNLL.write_doc2conll(doc, filename)
