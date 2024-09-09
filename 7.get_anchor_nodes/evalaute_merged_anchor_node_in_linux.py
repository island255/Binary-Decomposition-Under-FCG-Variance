import json
import os
import pickle
import re
from multiprocessing import Pool

from tqdm import tqdm


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def merge_duplicate_node(G):
    nodes_list = list(G.nodes())

    str_pattern = re.compile(r".*(_[0-9])$")
    for node in nodes_list:
        if str_pattern.match(node):
            node_strip = node[:-2]
            if node_strip in nodes_list:
                node_i_successors = list(G.successors(node))
                node_j_predecessors = list(G.predecessors(node))
                for node_i in node_i_successors:
                    G.add_edge(node_strip, node_i)
                for node_j in node_j_predecessors:
                    G.add_edge(node_j, node_strip)
                G.remove_node(node)
    return G


def get_common_nodes(O0_fcg, O3_fcg):
    nodes_O0 = list(O0_fcg.nodes())
    nodes_O3 = list(O3_fcg.nodes())
    common_nodes = list(set(nodes_O0).intersection(set(nodes_O3)))
    return common_nodes


def traverse_from_common_nodes(O0_fcg, common_nodes):
    inlining_communities_O0 = []
    for c_node in common_nodes:
        c_community = [c_node]
        c_node_successors = list(O0_fcg.successors(c_node))
        while c_node_successors:
            s_node = c_node_successors.pop()
            if s_node not in common_nodes and s_node not in c_community:
                c_community.append(s_node)
                c_node_successors += list(O0_fcg.successors(s_node))
        inlining_communities_O0.append(c_community)
    return inlining_communities_O0


def identify_inlined_functions(O0_mapping):
    O0_inlined_functions = []
    for bf in O0_mapping:
        bf_mapped_sfs = O0_mapping[bf]
        if len(bf_mapped_sfs) > 1:
            for sf in bf_mapped_sfs:
                sf_name = sf[1]
                if sf_name != bf:
                    O0_inlined_functions.append(sf_name)
    return O0_inlined_functions


def remove_inlined_node(common_nodes, O0_mapping, O3_mapping):
    normal_common_nodes = []
    O0_inlined_functions = identify_inlined_functions(O0_mapping)
    O3_inlined_functions = identify_inlined_functions(O3_mapping)
    for node in common_nodes:
        if node in O0_inlined_functions or node in O3_inlined_functions:
            continue
        else:
            normal_common_nodes.append(node)
    return normal_common_nodes


def identify_inlining_communities(O0_fcg, O3_fcg, O0_mapping, O3_mapping, anchor_nodes):
    # common_nodes = get_common_nodes(O0_fcg, O3_fcg)
    # common_nodes = remove_inlined_node(common_nodes, O0_mapping, O3_mapping)
    common_nodes = anchor_nodes
    inlining_communities_O0 = traverse_from_common_nodes(O0_fcg, common_nodes)
    inlining_communities_O3 = traverse_from_common_nodes(O3_fcg, common_nodes)
    return inlining_communities_O0, inlining_communities_O3, common_nodes


def summarize_mapping_statistics(cluster_to_cluster_mappings, cluster_mapping_statistics=None):
    wrong_clusters = {}
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
        if max_similarity != 1:
            wrong_clusters[cluster1] = cluster_to_cluster_mappings[cluster1]
        cluster_mapping_statistics[cluster1_len].append(max_similarity)
    return cluster_mapping_statistics, wrong_clusters


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


def evaluate_generated_clusters(O0_cluster, O3_cluster, O0_mapping, O3_mapping):
    normal_cluster_to_cluster_mappings = {}
    inlining_cluster_to_cluster_mappings = {}
    O0_mapping_to_sf, O0_cluster_to_inlining_flag = get_bf_mapped_sfs(O0_cluster, O0_mapping)
    O3_mapping_to_sf, O3_cluster_to_inlining_flag = get_bf_mapped_sfs(O3_cluster, O3_mapping)
    for O3_com in O3_mapping_to_sf:
        O3_com_mapped_sfs = O3_mapping_to_sf[O3_com]
        if not O3_com_mapped_sfs:
            continue
        if not O3_cluster_to_inlining_flag[O3_com]:
            normal_cluster_to_cluster_mappings["+".join(list(O3_com))] = {}
        else:
            inlining_cluster_to_cluster_mappings["+".join(list(O3_com))] = {}
        for O0_com in O0_mapping_to_sf:
            O0_com_mapped_sfs = O0_mapping_to_sf[O0_com]
            if set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)):
                similarity = len(list(set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)))) * 2 / \
                             (len(list(set(O3_com_mapped_sfs))) + len(list(set(O0_com_mapped_sfs))))
                if not O3_cluster_to_inlining_flag[O3_com]:
                    normal_cluster_to_cluster_mappings["+".join(list(O3_com))]["+".join(list(O0_com))] = similarity
                else:
                    inlining_cluster_to_cluster_mappings["+".join(list(O3_com))]["+".join(list(O0_com))] = similarity
    return {"normal_cluster_to_cluster_mappings": normal_cluster_to_cluster_mappings,
            "inlining_cluster_to_cluster_mappings": inlining_cluster_to_cluster_mappings}


def get_fcg_files(FCG_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(FCG_folder):
        project_folder = os.path.join(FCG_folder, project_name)
        for binary_fcg_name in os.listdir(project_folder):
            if not binary_fcg_name.endswith("fcg_pkl"):
                continue
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


def generate_cmds(fcg_files, mapping_folder, anchor_folder):
    cmd_list = []
    for binary_name in fcg_files:
        binary_to_fcg_files = fcg_files[binary_name]
        cmd_list.append([binary_name, binary_to_fcg_files, mapping_folder, anchor_folder])
    return cmd_list


def get_mapping_file(fcg_file1, mapping_folder):
    binary_fcg_pkl_name1 = os.path.basename(fcg_file1.replace(".i64.fcg.fcg_pkl", "")) + "_function_mapping.json"
    binary_project_name1 = os.path.basename(os.path.dirname(fcg_file1))
    mapping_file1 = os.path.join(mapping_folder, binary_project_name1, binary_fcg_pkl_name1)
    return mapping_file1


def run_anchor_node_generation(cmd):
    merged_anchor = r"/data1/jiaang/binkit2/7.anchor_node_identification/merged_anchor"
    binary_name, binary_to_fcg_files, mapping_folder, anchor_folder = cmd
    for index1 in range(0, len(binary_to_fcg_files)):
        for index2 in range(0, len(binary_to_fcg_files)):
            if index1 == index2:
                continue
            fcg_file1 = binary_to_fcg_files[index1]
            fcg_file2 = binary_to_fcg_files[index2]
            fcg1 = read_pickle(fcg_file1)
            fcg2 = read_pickle(fcg_file2)

            mapping_file1 = get_mapping_file(fcg_file1, mapping_folder)
            mapping_file2 = get_mapping_file(fcg_file2, mapping_folder)
            mapping1 = read_json(mapping_file1)
            mapping2 = read_json(mapping_file2)

            merged_anchor_file = os.path.join(merged_anchor, binary_name, binary_name + ".json")
            anchor_nodes = read_json(merged_anchor_file)
            inlining_communities_1, inlining_communities_2, anchor_nodes = \
                identify_inlining_communities(fcg1, fcg2, mapping1, mapping2, anchor_nodes)
            cluster_to_cluster_mappings = evaluate_generated_clusters(inlining_communities_1, inlining_communities_2,
                                                                      mapping1, mapping2)
            normal_cluster_mapping_statistics, normal_wrong_clusters = summarize_mapping_statistics(
                cluster_to_cluster_mappings["normal_cluster_to_cluster_mappings"])
            inlining_cluster_to_cluster_mappings, inlining_wrong_clusters = summarize_mapping_statistics(
                cluster_to_cluster_mappings["inlining_cluster_to_cluster_mappings"])
            cluster_mapping_statistics = {"normal": normal_cluster_mapping_statistics,
                                          "inlining": inlining_cluster_to_cluster_mappings}

            wrong_clusters = {"normal": normal_wrong_clusters, "inlining": inlining_wrong_clusters}

            anchor_info = {"anchor_node": anchor_nodes, "statistics": cluster_mapping_statistics,
                           "wrong_clusters": wrong_clusters}

            result_dir = os.path.join(anchor_folder, binary_name)
            if not os.path.exists(result_dir):
                try:
                    os.makedirs(result_dir)
                except:
                    pass

            result_file = os.path.join(result_dir, os.path.basename(mapping_file1.replace("_function_mapping.json", ""))
                                       + "+" + os.path.basename(mapping_file2).replace("_function_mapping.json",
                                                                                       "") + ".json")
            write_json(result_file, anchor_info)


def run_anchor_node_generation_dispatcher(cmd_list):
    print("running evaluation")
    process_num = 4
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_anchor_node_generation, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def get_anchor_node_in_linux():
    FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    arch = "clang-4.0_x86_64"
    fcg_files = get_fcg_files(FCG_folder, arch)
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"
    anchor_folder = r"/data1/jiaang/binkit2/7.anchor_node_identification/evaluate_merged_anchor"
    cmd_list = generate_cmds(fcg_files, mapping_folder, anchor_folder)
    run_anchor_node_generation_dispatcher(cmd_list)


if __name__ == '__main__':
    get_anchor_node_in_linux()
