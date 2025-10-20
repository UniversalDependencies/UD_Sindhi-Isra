cp not-to-release/xpos_features/sd_780_part_A.conllu sd_isra-ud-test.conllu
cat not-to-release/xpos_features/*_md_* >> sd_isra-ud-test.conllu

cp not-to-release/xpos_features/sd_780_part_B.conllu sd_isra-ud-dev.conllu
cat not-to-release/xpos_features/adabi_0.conllu >> sd_isra-ud-dev.conllu
cat not-to-release/xpos_features/adabi_1.conllu >> sd_isra-ud-dev.conllu

cp not-to-release/xpos_features/xpos_tagged_with_features.conllu sd_isra-ud-train.conllu

filenames=`ls not-to-release/xpos_features/* | grep -v sd_780 | grep -v _md_ | grep -v xpos_tagged_with_features | grep -v adabi_0.conllu | grep -v adabi_1.conllu`
for i in $filenames; do
    cat $i >> sd_isra-ud-train.conllu
done
