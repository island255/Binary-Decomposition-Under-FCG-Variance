import json
import os
import pickle
from multiprocessing import Pool

from tqdm import tqdm


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def get_mapped_acfg_files(acfg_disam_dir, project_binary_name, compilation):
    # a2ps-4.14_clang-10.0_arm_32_O0_a2ps_acfg_disasm.json
    mapping_acfg_disam_files = {}
    project_name, binary_name = project_binary_name.split("+")[0], project_binary_name.split("+")[1]
    for file_name in os.listdir(acfg_disam_dir):
        if file_name.startswith(project_name):
            elf_name = file_name.replace("_acfg_disasm.json", "")
            if elf_name.endswith(binary_name):
                if compilation in elf_name:
                    file_path = os.path.join(acfg_disam_dir, file_name)
                    optimization = elf_name.split(compilation)[-1].split("_")[1]
                    mapping_acfg_disam_files[optimization] = file_path
    return mapping_acfg_disam_files


def run_anchor_node_feature_extract_dispatcher(cmd_list):
    print("running evaluation")
    process_num = 4
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_anchor_node_feature_extract, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def extract_function_volume(acfg_disasm_content):
    function_volume = {}
    for IDB_name in acfg_disasm_content:
        for binary_address in acfg_disasm_content[IDB_name]:
            if binary_address == "arch":
                continue
            binary_address_16 = int(binary_address, 16)
            if binary_address_16 not in function_volume:
                function_volume[binary_address_16] = 0
            for bb in acfg_disasm_content[IDB_name][binary_address]["basic_blocks"]:
                bb_len = acfg_disasm_content[IDB_name][binary_address]["basic_blocks"][bb]["bb_len"]
                function_volume[binary_address_16] += bb_len
    return function_volume


def construct_FCG_adding_function_volume(FCG, function_to_volume):
    for node in FCG:
        # debug_info = FCG.nodes[node]
        start_address = FCG.nodes[node]["node_attribute"]["start_address"]
        if start_address in function_to_volume:
            function_volume = function_to_volume[start_address]
            FCG.nodes[node]["node_attribute"]["function_volume"] = function_volume

    return FCG


def extract_function_features(FCG_with_function_volume):
    node_features = {}
    nodes_list = list(FCG_with_function_volume.nodes())
    for node in nodes_list:
        if "node_attribute" in FCG_with_function_volume.nodes[node]:
            if "function_volume" in FCG_with_function_volume.nodes[node]["node_attribute"]:
                function_volume = FCG_with_function_volume.nodes[node]["node_attribute"]["function_volume"]
                in_degree = FCG_with_function_volume.in_degree(node)
                out_degree = FCG_with_function_volume.out_degree(node)
                node_features[node] = {"function_volume": function_volume, "in_degree": in_degree,
                                       "out_degree": out_degree}
    return node_features


def classify_nodes(node_features, anchor_nodes):
    normal_node_features = {}
    anchor_node_features = {}
    for node in node_features:
        if node in anchor_nodes:
            anchor_node_features[node] = node_features[node]
        else:
            normal_node_features[node] = node_features[node]
    return {"normal":normal_node_features, "anchor": anchor_node_features}


def run_anchor_node_feature_extract(cmd):
    project_binary_name, anchor_nodes, mapping_acfg_disam_files, mapped_fcg_files, result_path = cmd
    anchor_features_result_file = os.path.join(result_path, project_binary_name + ".json")
    if os.path.exists(anchor_features_result_file):
        return
    different_node_features = {}
    for optimization in mapping_acfg_disam_files:
        acfg_file_path = mapping_acfg_disam_files[optimization]
        acfg_disasm_content = read_json(acfg_file_path)
        function_to_volume = extract_function_volume(acfg_disasm_content)
        mapped_fcg_file_path = mapped_fcg_files[optimization]
        FCG = read_pickle(mapped_fcg_file_path)
        FCG_with_function_volume = construct_FCG_adding_function_volume(FCG, function_to_volume)
        node_features = extract_function_features(FCG_with_function_volume)
        different_node_features[optimization] = classify_nodes(node_features, anchor_nodes)
    write_json(anchor_features_result_file, different_node_features)


def get_mapped_fcg_files(FCG_folder, project_binary_name, compilation):
    mapped_fcg_files = {}
    project_name, binary_name = project_binary_name.split("+")[0], project_binary_name.split("+")[1]
    for file_name in os.listdir(os.path.join(FCG_folder, project_name)):
        if file_name.endswith(".i64.fcg.fcg_pkl"):
            if file_name.startswith(project_name):
                elf_name = file_name.replace(".i64.fcg.fcg_pkl", "")
                if elf_name.endswith(binary_name):
                    if compilation in elf_name:
                        file_path = os.path.join(FCG_folder, project_name, file_name)
                        optimization = elf_name.split(compilation)[-1].split("_")[1]
                        mapped_fcg_files[optimization] = file_path
    return mapped_fcg_files


def main():
    FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    acfg_disam_dir = r"/data1/jiaang/binkit2/0.preprocessing/IDA_scripts/IDA_acfg_disasm/acfg_disasm_dataset_I"
    merged_anchor_node_dir = r"/data1/jiaang/binkit2/7.anchor_node_identification/merged_anchor"
    compilation = "clang-4.0_x86_64"
    result_path = "/data1/jiaang/binkit2/7.anchor_node_identification/anchor_features"
    anchor_node_to_acfg_files = []
    for project_binary_name in os.listdir(merged_anchor_node_dir):
        anchor_file_path = os.path.join(merged_anchor_node_dir, project_binary_name, project_binary_name + ".json")
        anchor_nodes = read_json(anchor_file_path)
        mapping_acfg_disam_files = get_mapped_acfg_files(acfg_disam_dir, project_binary_name, compilation)
        mapped_fcg_files = get_mapped_fcg_files(FCG_folder, project_binary_name, compilation)
        anchor_node_to_acfg_files.append([project_binary_name, anchor_nodes, mapping_acfg_disam_files, mapped_fcg_files, result_path])
    write_json("anchor_node_to_acfg_files.json", anchor_node_to_acfg_files)
    run_anchor_node_feature_extract_dispatcher(anchor_node_to_acfg_files)


if __name__ == '__main__':
    main()
