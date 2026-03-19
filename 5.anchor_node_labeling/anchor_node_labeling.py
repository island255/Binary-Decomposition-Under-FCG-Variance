#encoding=utf-8
import json
import os
import pickle
import re
from multiprocessing import Pool
from functools import reduce
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


def get_common_nodes(fcgs):
    """
    获取一组FCG中的所有公共节点
    """
    if not fcgs:
        return []

    # 获取所有FCG的节点集合
    nodes_sets = [set(fcg.nodes()) for fcg in fcgs]

    # 计算所有集合的交集
    common_nodes = list(reduce(lambda x, y: x & y, nodes_sets))
    return common_nodes


def get_non_common_nodes(fcgs, common_nodes):
    """
    获取每个FCG中非公共的节点
    """
    non_common_nodes = []
    for fcg in fcgs:
        all_nodes = set(fcg.nodes())
        non_common = list(all_nodes - set(common_nodes))
        non_common_nodes.append(non_common)
    return non_common_nodes


def traverse_from_common_nodes(fcg, common_nodes):
    communities = []
    for c_node in common_nodes:
        community = [c_node]
        c_node_successors = list(fcg.successors(c_node))
        while c_node_successors:
            s_node = c_node_successors.pop()
            if s_node not in common_nodes and s_node not in community:
                community.append(s_node)
                c_node_successors += list(fcg.successors(s_node))
        communities.append(community)
    return communities


def identify_inlined_functions(mapping):
    inlined_functions = []
    for bf in mapping:
        bf_mapped_sfs = mapping[bf]
        if len(bf_mapped_sfs) > 1:
            for sf in bf_mapped_sfs:
                sf_name = sf[1]
                if sf_name != bf:
                    inlined_functions.append(sf_name)
    return inlined_functions


def remove_inlined_node(common_nodes, mappings):
    normal_common_nodes = []
    inlined_functions = []

    # 收集所有mapping中的内联函数
    for mapping in mappings:
        inlined_functions.extend(identify_inlined_functions(mapping))

    for node in common_nodes:
        if node in inlined_functions:
            continue
        else:
            normal_common_nodes.append(node)
    return normal_common_nodes


def extract_all_nodes_in_mapping(mapping):
    all_functions = []
    for bf in mapping:
        bf_mapped_sfs = mapping[bf]
        for sf in bf_mapped_sfs:
            sf_name = sf[1]
            all_functions.append(sf_name)
    return all_functions

def list_intersection(*lists):
    if not lists:
        return []
    # 将第一个列表转换为集合
    result = set(lists[0])
    # 依次与其他列表求交集
    for lst in lists[1:]:
        result.intersection_update(lst)
    return list(result)


def identify_non_inlined_nodes(mappings):
    function_list = []
    inlined_function_list = []
    for mapping in mappings:
        inlined_functions = identify_inlined_functions(mapping)
        functions = extract_all_nodes_in_mapping(mapping)
        inlined_function_list = list(set(inlined_function_list + inlined_functions))
        function_list.append(functions)
    common_nodes = list_intersection(*function_list)
    non_inlined_node = list(set(common_nodes).difference(inlined_function_list))
    return non_inlined_node



def identify_inlining_communities(fcgs, mappings):
    non_inlined_nodes = identify_non_inlined_nodes(mappings)
    # common_nodes = get_common_nodes(fcgs)
    common_nodes = non_inlined_nodes
    non_common_nodes = get_non_common_nodes(fcgs, non_inlined_nodes)
    # common_nodes = remove_inlined_node(non_inlined_nodes, mappings)

    return common_nodes, non_common_nodes, non_inlined_nodes


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


def get_bf_mapped_sfs(cluster, mapping):
    mapping_to_sf = {}
    for com in cluster:
        mapping_to_sf[tuple(com)] = []
        for bf in com:
            if bf not in mapping or mapping[bf] == []:
                continue
            else:
                for sf_dict in mapping[bf]:
                    sf_name = sf_dict[0].replace("/data1/jiaang/binkit2/Dataset/src/", "") + "+" + sf_dict[1]
                    mapping_to_sf[tuple(com)].append(sf_name)
    return mapping_to_sf


def extract_compilation_info(fcg_name):
    """
    从fcg文件名中提取编译条件信息
    示例输入: a2ps-4.14_clang-4.0_arm_32_O0_a2ps.i64.fcg.fcg_pkl
    返回: clang-4.0_arm_32_O0
    """
    parts = fcg_name.split("_")
    if len(parts) >= 5:
        return "_".join(parts[1:-1])  # 去掉项目名和文件名部分
    return "unknown"


def evaluate_generated_clusters(clusters, mappings, fcg_names):
    all_results = []

    # 比较每对cluster
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            cluster_to_cluster_mappings = {}

            mapping_to_sf1 = get_bf_mapped_sfs(clusters[i], mappings[i])
            mapping_to_sf2 = get_bf_mapped_sfs(clusters[j], mappings[j])

            for com1 in mapping_to_sf1:
                com1_mapped_sfs = mapping_to_sf1[com1]
                if not com1_mapped_sfs:
                    continue

                cluster_to_cluster_mappings["+".join(list(com1))] = {}

                for com2 in mapping_to_sf2:
                    com2_mapped_sfs = mapping_to_sf2[com2]
                    if set(com1_mapped_sfs).intersection(set(com2_mapped_sfs)):
                        similarity = len(list(set(com1_mapped_sfs).intersection(set(com2_mapped_sfs)))) * 2 / \
                                     (len(list(set(com1_mapped_sfs))) + len(list(set(com2_mapped_sfs))))
                        cluster_to_cluster_mappings["+".join(list(com1))]["+".join(list(com2))] = similarity

            # 获取两个FCG的编译条件
            comp1 = extract_compilation_info(fcg_names[i])
            comp2 = extract_compilation_info(fcg_names[j])

            all_results.append({
                "cluster_to_cluster_mappings": cluster_to_cluster_mappings,
                "compilation_pair": f"{comp1} vs {comp2}",
                "pair_indices": (i, j)
            })

    return all_results


def get_fcg_files(FCG_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(FCG_folder):
        project_folder = os.path.join(FCG_folder, project_name)
        for binary_fcg_name in os.listdir(project_folder):
            if not binary_fcg_name.endswith("fcg_pkl"):
                continue
            if "mips" in binary_fcg_name or "clang-13.0" in binary_fcg_name:
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


def get_mapping_file(fcg_file, mapping_folder):
    binary_fcg_pkl_name = os.path.basename(fcg_file.replace(".i64.fcg.fcg_pkl", "")) + "_function_mapping.json"
    binary_project_name = os.path.basename(os.path.dirname(fcg_file))
    mapping_file = os.path.join(mapping_folder, binary_project_name, binary_fcg_pkl_name)
    return mapping_file


def run_anchor_node_generation(cmd):
    binary_name, binary_to_fcg_files, mapping_folder, anchor_folder = cmd

    # 读取所有FCG和mapping文件
    fcgs = []
    mappings = []
    fcg_names = [os.path.basename(f) for f in binary_to_fcg_files]
    for fcg_file in binary_to_fcg_files:
        fcgs.append(read_pickle(fcg_file))
        mappings.append(read_json(get_mapping_file(fcg_file, mapping_folder)))

    # 处理一组FCG
    common_nodes, non_common_nodes, non_inlined_nodes = identify_inlining_communities(fcgs, mappings)

    # 为每个FCG记录其非公共节点
    non_common_nodes_info = []
    for i, nodes in enumerate(non_common_nodes):
        non_common_nodes_info.append({
            "fcg_file": fcg_names[i],
            "compilation": extract_compilation_info(fcg_names[i]),
            "non_common_nodes": nodes
        })

    anchor_info = {
        "anchor_node": common_nodes,
        "non_inlined_nodes": non_inlined_nodes,
        "non_common_nodes": non_common_nodes_info,
        "fcg_files": fcg_names
    }

    result_dir = os.path.join(anchor_folder, binary_name)
    if not os.path.exists(result_dir):
        try:
            os.makedirs(result_dir)
        except:
            pass

    # 生成结果文件名

    result_file = os.path.join(result_dir, binary_name+ ".json")

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
    arch = ""
    fcg_files = get_fcg_files(FCG_folder, arch)
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"
    anchor_folder = r"/data1/jiaang/binkit2/7.anchor_node_labeling/anchor"
    cmd_list = generate_cmds(fcg_files, mapping_folder, anchor_folder)
    run_anchor_node_generation_dispatcher(cmd_list)


if __name__ == '__main__':
    get_anchor_node_in_linux()