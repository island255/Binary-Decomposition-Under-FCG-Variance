# N2NMatcher
Repository for Paper “Binary Decomposition Under FCG Variance”

## Dataset Labeling

Dataset is from Binkit, please refer to https://github.com/SoftSec-KAIST/BinKit

1. run `0.prerpocessing\IDA_scripts\IDA_acfg_disasm` to extract Address-to-Functions Mappings 

please refer to https://github.com/Cisco-Talos/binary_function_similarity/tree/main/IDA_scripts/IDA_acfg_disasm

2. run `1.function_mapping_labeling\linux_run_source2binary_mapping_using_treesitter_and_ida.py` to extract Source line-to-function mappings and Binary2Source Function Mappings

please refer to https://github.com/island255/TOSEM2022

3. run `2.Binary_FCG_extraction\IDA_fcg_extractor\run_IDA_on_all_binaries.py` to extract nodes and edges of FCGs in binaries

4. run `3.FCG_construction\FCG_construction.py` to construct the FCGs from the nodes and edges

## FCG Variance Anlysis

1. run `3.FCG_construction\FCG_statistics_evaluation.py` to analyze the changes of FCGs

2. run `4.construct_function_mapping\three_types_of_mappings\construct_three_types_of_mapping.py` and `4.construct_function_mapping\three_types_of_mappings\construct_cross_compiler_and_opt.py` to construct three types of mapping in cross-optimization evaluation and cross-compiler evaluation


## Existing Works Replication

1. run `4.construct_function_mapping\construct_function_mapping.py` to analyze the node and neighbor difference

2. run `5.implement_strategy_of_existing_works\BMVUL\run_BMVul_on_Binkit.py` and `5.implement_strategy_of_existing_works\BMVUL\run_BMVul_on_Binkit.py` to replicate BMVul and ModX

3. run `6.evaluate_existing_work\evaluate_BMVul.py` and `6.evaluate_existing_work\evaluate_ModX.py` to evaluate BMVul and ModX

## Optimal Decomposition

1. run `7.anchor_node_labeling\anchor_node_labeling.py` to label the non-inlined functions

2. run `7.anchor_node_labeling\using_anchor_to_evaluate_existing_works\using_anchor_to_evaulate_existing_works.py` to compare existing works with the optimal decomposition.

## License

The code in this repository is licensed under the MIT License, however, some models and scripts in dataset labeling may depend on code with different licenses. Please refer to their original repositories. 
