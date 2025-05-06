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
  
5. run `4.construct_function_mapping\construct_function_mapping.py` to obatain the binary2binary function mappings and function call mappings.

## Existing Works Replication

1. run `4.construct_function_mapping\draw_neighbor_difference.py` and `4.construct_function_mapping\draw_opt_difference.py` to analyze the node and neighbor difference

2. run `5.implement_strategy_of_existing_works\BMVUL\run_BMVul_on_Binkit.py` and `5.implement_strategy_of_existing_works\BMVUL\run_BMVul_on_Binkit.py` to replicate BMVul and ModX

3. run `6.evaluate_existing_work\evaluate_BMVul_top10.py` and `6.evaluate_existing_work\evaluate_ModX_top10.py` to evaluate BMVul and ModX

## N2NMatcher

1. run `7.get_anchor_nodes\anchor_node_labeling.py` to label the anchor nodes and normal nodes

2. run `8.classify_anchor_node_and_normal_nodes\extract_anchor_features.py` to extract features for nodes and `8.classify_anchor_node_and_normal_nodes\convert_node_features_to_vectors_with_function_name.py` to convert feature into vectors

3. run `8.classify_anchor_node_and_normal_nodes\reorganize_features_by_arch.py` to divide the features file into different archs, and run `8.classify_anchor_node_and_normal_nodes\train_ensemble_classifier.py` to train N2NMatcher and other methods on anchor node identification.

4. run `9.apply_classifier_to_fcg_nodes\run_classifier_on_fcg.py` to iterate N2NMatcher 10 times to cover all projcts in testing and run `9.apply_classifier_to_fcg_nodes\evaluation\extract_N2NMatcher_anchor_nodes.py` to evaluate N2NMatcher on binary decomposition.

## License

The code in this repository is licensed under the MIT License, however, some models and scripts in dataset labeling may depend on code with different licenses. Please refer to their original repositories. 
