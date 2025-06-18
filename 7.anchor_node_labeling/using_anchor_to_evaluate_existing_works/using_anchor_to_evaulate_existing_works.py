# encoding=utf-8
import os
import json
import pickle
from collections import defaultdict
from multiprocessing import Pool

from tqdm import tqdm

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)

def get_ModX_cluster_files(ModX_results_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(ModX_results_folder):
        project_folder = os.path.join(ModX_results_folder, project_name)
        for binary_json in os.listdir(project_folder):
            if "_mips_" in binary_json or "clang-13.0" in binary_json:
                continue
            binary_path = os.path.join(project_folder, binary_json)
            binary_name = binary_json[:-5].split("_")[-1]
            project_binary_name = project_name + "+" + binary_name
            if project_binary_name not in binary_name_to_compilations:
                binary_name_to_compilations[project_binary_name] = []
            if arch:
                if arch in binary_json:
                    binary_name_to_compilations[project_binary_name].append(binary_path)
            else:
                binary_name_to_compilations[project_binary_name].append(binary_path)
    return binary_name_to_compilations


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)



def traverse_from_common_nodes(fcg, common_nodes):
    common_nodes = list(set(common_nodes).intersection(set(fcg.nodes())))
    inlining_communities = []
    for c_node in common_nodes:
        c_community = [c_node]
        c_node_successors = list(fcg.successors(c_node))
        while c_node_successors:
            s_node = c_node_successors.pop()
            if s_node not in common_nodes and s_node not in c_community:
                c_community.append(s_node)
                c_node_successors += list(fcg.successors(s_node))
        inlining_communities.append(c_community)

    if not inlining_communities:
        inlining_communities += list(fcg.nodes())
    return inlining_communities


def run_anchor_node_generation(cmd):
    binary_name, fcg_file, mapping_folder, result_folder, merged_anchor = cmd
    merged_anchor_file = os.path.join(merged_anchor, binary_name, binary_name + ".json")
    anchor_nodes = read_json(merged_anchor_file)["anchor_node"]
    result_dir = os.path.join(result_folder, binary_name)
    binary_compilation_name = os.path.basename(fcg_file).replace(".i64.fcg.fcg_pkl", "")
    result_file = os.path.join(result_dir, binary_compilation_name + ".json")
    if os.path.exists(result_file):
        return
    fcg = read_pickle(fcg_file)
    inlining_communities = traverse_from_common_nodes(fcg, anchor_nodes)

    if not os.path.exists(result_dir):
        try:
            os.makedirs(result_dir)
        except:
            pass

    write_json(result_file, inlining_communities)




def run_anchor_node_generation_dispatcher(cmd_list):
    print("generating communities...")
    process_num = 16
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_anchor_node_generation, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def generate_cmds(fcg_files, mapping_folder, result_folder, anchor_folder):
    cmd_list = []
    for binary_name in fcg_files:
        binary_to_fcg_files = fcg_files[binary_name]
        for fcg_file in binary_to_fcg_files:
            cmd_list.append([binary_name, fcg_file, mapping_folder, result_folder, anchor_folder])
    return cmd_list


def get_fcg_files(FCG_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(FCG_folder):
        project_folder = os.path.join(FCG_folder, project_name)
        for binary_fcg_name in os.listdir(project_folder):
            if not binary_fcg_name.endswith("fcg_pkl"):
                continue
            if "_mips_" in binary_fcg_name or "clang-13.0" in binary_fcg_name:
                continue
            # if "x86_64" not in binary_fcg_name: # testing
            #     continue
            binary_path = os.path.join(project_folder, binary_fcg_name)
            binary_name = binary_fcg_name.replace(".i64.fcg.fcg_pkl", "").split("_")[-1]
            project_binary_name = project_name + "+" + binary_name
            if project_binary_name not in binary_name_to_compilations:
                binary_name_to_compilations[project_binary_name] = []
            if arch:
                if arch in binary_fcg_name:
                    binary_name_to_compilations[project_binary_name].append(binary_path)
            else:
                binary_name_to_compilations[project_binary_name].append(binary_path)
    return binary_name_to_compilations


def run_ModX_community_evaluation_dispatcher(cmd_list):
    print("comparing communities...")
    process_num = 16
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_ModX_community_evaluation, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def get_bf_mapped_sfs(O0_cluster, O0_mapping):
    O0_mapping_to_sf = {}
    O0_cluster_to_inlining_flag = {}
    for com in O0_cluster:
        O0_mapping_to_sf[tuple(com)] = []
        inlining_flag = False
        for bf in com:
            if bf not in O0_mapping or O0_mapping[bf] == []:
                continue
                # print("{} not in mapping".format(bf))
            else:
                if len(O0_mapping[bf]) > 1:
                    inlining_flag = True
                for sf_dict in O0_mapping[bf]:
                    sf_name = sf_dict[0].replace("/data1/jiaang/binkit2/Dataset/src/", "") + "+" + sf_dict[1]
                    O0_mapping_to_sf[tuple(com)].append(sf_name)
        O0_cluster_to_inlining_flag[tuple(com)] = inlining_flag
    return O0_mapping_to_sf, O0_cluster_to_inlining_flag



def evaluate_generated_clusters(cluster, anchor_communities, mapping):
    cluster_to_cluster_mappings = {}
    mapping_to_sf1, cluster_to_inlining_flag1 = get_bf_mapped_sfs(cluster, mapping)
    mapping_to_sf2, cluster_to_inlining_flag2 = get_bf_mapped_sfs(anchor_communities, mapping)
    for com2 in mapping_to_sf2:
        com2_mapped_sfs = mapping_to_sf2[com2]
        if not com2_mapped_sfs:
            continue
        cluster_to_cluster_mappings["+".join(list(com2))] = {}
        for com1 in mapping_to_sf1:
            com1_mapped_sfs = mapping_to_sf1[com1]
            if set(com2_mapped_sfs).intersection(set(com1_mapped_sfs)):
                similarity = len(list(set(com2_mapped_sfs).intersection(set(com1_mapped_sfs)))) * 2 / \
                             (len(list(set(com2_mapped_sfs))) + len(list(set(com1_mapped_sfs))))
                cluster_to_cluster_mappings["+".join(list(com2))]["+".join(list(com1))] = similarity
    return cluster_to_cluster_mappings


def summarize_mapping_statistics(cluster_to_cluster_mappings, cluster_mapping_statistics=None):
    if cluster_mapping_statistics is None:
        cluster_mapping_statistics = {}
    for cluster1 in cluster_to_cluster_mappings:
        cluster1_list = cluster1.split("+")
        cluster1_len = len(cluster1_list)
        if cluster1_len not in cluster_mapping_statistics:
            cluster_mapping_statistics[cluster1_len] = []
        max_similarity = 0
        for cluster2 in cluster_to_cluster_mappings[cluster1]:
            similarity = cluster_to_cluster_mappings[cluster1][cluster2]
            if similarity >= max_similarity:
                max_similarity = similarity
        cluster_mapping_statistics[cluster1_len].append(max_similarity)
    return cluster_mapping_statistics


def evaluate_cluster_by_anchor_community(cluster, anchor_communities, mapping):
    cluster_to_cluster_mappings = evaluate_generated_clusters(cluster, anchor_communities, mapping)
    cluster_mapping_statistics = summarize_mapping_statistics(
        cluster_to_cluster_mappings)
    return cluster_mapping_statistics



def get_BMVul_cluster_files(method_results_folder, arch):
    binary_name_to_compilations = {}
    for project_name in os.listdir(method_results_folder):
        project_folder = os.path.join(method_results_folder, project_name)
        for binary_pkl in os.listdir(project_folder):
            if "_mips_" in binary_pkl or "clang-13.0" in binary_pkl:
                continue
            binary_path = os.path.join(project_folder, binary_pkl, "clusters.json")
            binary_name = binary_pkl[:-16].split("_")[-1]
            project_binary_name = project_name + "+" + binary_name
            if project_binary_name not in binary_name_to_compilations:
                binary_name_to_compilations[project_binary_name] = []
            if arch:
                if arch in binary_pkl:
                    binary_name_to_compilations[project_binary_name].append(binary_path)
            else:
                binary_name_to_compilations[project_binary_name].append(binary_path)
    return binary_name_to_compilations


def extract_clusters(cluster_content):
    cluster = []
    for community_dict in cluster_content:
        community_nodes_dict = community_dict["nodes"]
        community_nodes = []
        for node_dict in community_nodes_dict:
            function_name = node_dict["id"]
            community_nodes.append(function_name)
        cluster.append(community_nodes)
    return cluster


def run_ModX_community_evaluation(cmd):
    binary_name, cluster_file, mapping_folder, community_folder, result_folder, evaluate_method = cmd
    modx_result_folder = os.path.join(result_folder, binary_name)
    if not os.path.exists(modx_result_folder):
        try:
            os.makedirs(modx_result_folder)
        except OSError as e:
            pass
    if evaluate_method == "ModX":
        binary_full_name = os.path.basename(cluster_file)
    else:
        binary_full_name = os.path.basename(os.path.dirname(cluster_file)).replace(".i64.fcg.fcg_pkl", ".json")
    modx_result_path = os.path.join(modx_result_folder, binary_full_name)
    if os.path.exists(modx_result_path):
        return
    if evaluate_method == "ModX":
        cluster = read_json(cluster_file)
    elif evaluate_method == "BMVul":
        cluster_content = read_json(cluster_file)
        cluster = extract_clusters(cluster_content)
    # community_folder = r"/data1/jiaang/binkit2/7.anchor_node_labeling/using_anchor_to_evaluate_existing_works/anchor_communities"
    anchor_community_file_path = os.path.join(community_folder, binary_name, binary_full_name)
    mapping_file = os.path.join(mapping_folder, binary_name.split("+")[0],
                                binary_full_name.replace(".json", "_function_mapping.json"))


    anchor_communities = read_json(anchor_community_file_path)
    mapping = read_json(mapping_file)
    ModX_evaluate_result = evaluate_cluster_by_anchor_community(cluster, anchor_communities, mapping)
    write_json(modx_result_path, ModX_evaluate_result)


def generate_cmds_for_evaluation(cluster_files, mapping_folder, community_folder, result_folder, evaluate_method):
    cmd_list = []
    for binary_name in cluster_files:
        binary_to_cluster_files = cluster_files[binary_name]
        for cluster_file in binary_to_cluster_files:
            cmd_list.append([binary_name, cluster_file, mapping_folder, community_folder, result_folder, evaluate_method])
    return cmd_list


def main():
    community_folder = r"/data1/jiaang/binkit2/7.anchor_node_labeling/using_anchor_to_evaluate_existing_works/anchor_communities"
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"
    arch = "x86_64"
    # FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    # fcg_files = get_fcg_files(FCG_folder, arch)
    # anchor_folder = "/data1/jiaang/binkit2/7.anchor_node_labeling/anchor"
    # cmd_list = generate_cmds(fcg_files, mapping_folder, community_folder, anchor_folder)
    # run_anchor_node_generation_dispatcher(cmd_list)

    evaluate_method_list = ["ModX", "BMVul"]
    for evaluate_method in evaluate_method_list:
        method_results_folder = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/" + evaluate_method + "/results/"
        result_folder = r"/data1/jiaang/binkit2/7.anchor_node_labeling/using_anchor_to_evaluate_existing_works/" + evaluate_method + "/results"
        if evaluate_method == "ModX":
            cluster_files = get_ModX_cluster_files(method_results_folder, arch)
        elif evaluate_method == "BMVul":
            cluster_files = get_BMVul_cluster_files(method_results_folder, arch)
        cmd_list = generate_cmds_for_evaluation(cluster_files, mapping_folder, community_folder, result_folder, evaluate_method)
        run_ModX_community_evaluation_dispatcher(cmd_list)


if __name__ == '__main__':
    main()