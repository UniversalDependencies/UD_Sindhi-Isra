Directories:

tokenization: several data files of stories or news articles combined into one, hand tokenized and slowly improved over time.
tokenization_fixes: some fixed / resplit sentences, gradually being applied to the dataset as the featurization reaches there

dependencies: the tokenization data file with upos and dependency trees.  some sentences are reparsed from the MD dataset or elsewhere
mltwist_dependencies: raw datafiles of dependencies from MLtwist
upos: an initial UPOS tagged file for training early taggers.  not maintained long term
edits: some updates of those files.  not maintained long term

xpos_standard: initial xpos & feature tagging.  roughly 100 hand-chosen tagged sentences with features
xpos_features: sentences from the dependencies folder, now with xpos and features.  the xpos_standard files are kept separate currently

lemmas: files with word,POS,lemma.  a subdirectory has unchecked versions of those files

agreement: two different annotations of the same dependency file, from Shafi and Sarwat.  A script for analyzing them
scripts: various tools for merging edited conllu files or the lemmas back into the current annotations



The test file is currently sd_780_A from the xpos_features directory.  The plan is to add all of the MD- sentences as well.
The dev file is sd_780_B

Everything else will go into train (at least at first)

