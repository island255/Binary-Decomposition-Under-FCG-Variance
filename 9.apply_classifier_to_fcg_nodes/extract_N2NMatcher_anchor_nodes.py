import json
import os
import pickle
import time
from multiprocessing import Pool

from tqdm import tqdm


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def write_pickle(pickle_file, obj):
    with open(pickle_file, "wb") as f:
        pickle.dump(obj, f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)


def find_char_positions(s, char):
    positions = []
    for i in range(len(s)):
        if s[i] == char:
            positions.append(i)
    return positions


def get_binary_fcg_labels(results_folder):
    binary_fcg_labels_file = "binary_fcg_labels.json"
    if not os.path.exists(binary_fcg_labels_file):
        print("summarize fcg labels")
        method_list = list(os.listdir(results_folder))
        binary_fcg_labels = {}
        for method in method_list:
            method_result_folder = os.path.join(results_folder, method)
            for result_file_pickle in os.listdir(method_result_folder):
                result_file_pickle_path = os.path.join(method_result_folder, result_file_pickle)
                result_file_pickle_content = read_pickle(result_file_pickle_path)
                function_labels, all_times = result_file_pickle_content
                test_binary_functions, testing_label, predicted_labels = function_labels
                for index, test_binary_func in enumerate(test_binary_functions):
                    project_binary_name, opt, function_name = test_binary_func
                    splitter_position = find_char_positions(project_binary_name, "+")
                    project_name = project_binary_name[:splitter_position[0]]
                    binary_name = project_binary_name[splitter_position[0]+1:]
                    label = testing_label[index]
                    # print(test_binary_functions)
                    if project_name not in binary_fcg_labels:
                        binary_fcg_labels[project_name] = {}
                    if binary_name not in binary_fcg_labels[project_name]:
                        binary_fcg_labels[project_name][binary_name] = {}
                    if opt not in binary_fcg_labels[project_name][binary_name]:
                        binary_fcg_labels[project_name][binary_name][opt] = {}
                    binary_fcg_labels[project_name][binary_name][opt][function_name] = int(label)
        write_json(binary_fcg_labels_file, binary_fcg_labels)
    else:
        binary_fcg_labels = read_json(binary_fcg_labels_file)
    return binary_fcg_labels


def traverse_from_common_nodes(fcg, anchor_nodes):
    inlining_communities = []
    for c_node in anchor_nodes:
        if c_node not in fcg:
            # print("{} not in fcg".format(c_node))
            continue
        c_community = [c_node]
        c_node_successors = list(fcg.successors(c_node))
        while c_node_successors:
            s_node = c_node_successors.pop()
            if s_node not in anchor_nodes and s_node not in c_community:
                c_community.append(s_node)
                c_node_successors += list(fcg.successors(s_node))
        inlining_communities.append(c_community)
    return inlining_communities


def extract_anchor_nodes(binary_fcg_func_labels):
    anchor_nodes = []
    for func_name in binary_fcg_func_labels:
        if binary_fcg_func_labels[func_name]:
            anchor_nodes.append(func_name)
    return anchor_nodes


def extract_anchor_communities(binary_fcg_path, binary_fcg_func_labels):
    binary_fcg = read_pickle(binary_fcg_path)
    anchor_nodes = extract_anchor_nodes(binary_fcg_func_labels)
    anchor_community = traverse_from_common_nodes(binary_fcg, anchor_nodes)
    return anchor_community


def extract_binary_name_from_fcg_file_name(binary_fcg_path):
    binary_name = binary_fcg_path.replace(".i64.fcg.fcg_pkl", "").split("_")[-1]
    opt = binary_fcg_path.replace(".i64.fcg.fcg_pkl", "").split("_")[-2]
    return binary_name, opt


def traverse_fcg_files(FCG_path, binary_fcg_labels):
    running_time = []
    binary_name_to_fcg_communities = {}
    for project_name in binary_fcg_labels:
        print("processing project {}, use anchor to divide fcgs ...".format(project_name))
        fcg_project_folder = os.path.join(FCG_path, project_name)
        for binary_fcg_name in tqdm(os.listdir(fcg_project_folder)):
            if not binary_fcg_name.endswith(".fcg_pkl") or "clang-4.0_x86_64" not in binary_fcg_name:
                continue
            binary_fcg_path = os.path.join(fcg_project_folder, binary_fcg_name)
            binary_name, opt = extract_binary_name_from_fcg_file_name(binary_fcg_path)
            if binary_name not in binary_fcg_labels[project_name] or opt not in binary_fcg_labels[project_name][binary_name]:
                continue
            binary_fcg_func_labels = binary_fcg_labels[project_name][binary_name][opt]
            start_time = time.time()
            anchor_community = extract_anchor_communities(binary_fcg_path, binary_fcg_func_labels)
            end_time = time.time()
            running_time.append(end_time - start_time)
            project_binary_name = project_name + "+" + binary_name
            if project_binary_name not in binary_name_to_fcg_communities:
                binary_name_to_fcg_communities[project_binary_name] = {}
            binary_name_to_fcg_communities[project_binary_name][binary_fcg_path] = anchor_community
    return binary_name_to_fcg_communities, running_time


def get_mapping_file(fcg_file1, mapping_folder):
    binary_fcg_pkl_name1 = os.path.basename(fcg_file1.replace(".i64.fcg.fcg_pkl", "")) + "_function_mapping.json"
    binary_project_name1 = os.path.basename(os.path.dirname(fcg_file1))
    mapping_file1 = os.path.join(mapping_folder, binary_project_name1, binary_fcg_pkl_name1)
    return mapping_file1


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


def evaluate_community_similarities(cmd):
    project_binary_name, binary_fcg_to_communities = cmd
    results_folder = r"/data1/jiaang/binkit2/9.apply_classifier_to_fcg_nodes/evaluate_results_new"
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"
    fcg_path_list = list(binary_fcg_to_communities.keys())
    for index1 in range(0, len(fcg_path_list)):
        for index2 in range(0, len(fcg_path_list)):
            if index1 == index2:
                continue
            fcg_file1 = fcg_path_list[index1]
            fcg_file2 = fcg_path_list[index2]
            community1 = binary_fcg_to_communities[fcg_file1]
            community2 = binary_fcg_to_communities[fcg_file2]

            mapping_file1 = get_mapping_file(fcg_file1, mapping_folder)
            mapping_file2 = get_mapping_file(fcg_file2, mapping_folder)
            mapping1 = read_json(mapping_file1)
            mapping2 = read_json(mapping_file2)

            cluster_to_cluster_mappings = evaluate_generated_clusters(community1, community2, mapping1, mapping2)
            normal_cluster_mapping_statistics, normal_wrong_clusters = summarize_mapping_statistics(
                cluster_to_cluster_mappings["normal_cluster_to_cluster_mappings"])
            inlining_cluster_to_cluster_mappings, inlining_wrong_clusters = summarize_mapping_statistics(
                cluster_to_cluster_mappings["inlining_cluster_to_cluster_mappings"])
            cluster_mapping_statistics = {"normal": normal_cluster_mapping_statistics,
                                          "inlining": inlining_cluster_to_cluster_mappings}

            anchor_info = {"statistics": cluster_mapping_statistics}

            result_dir = os.path.join(results_folder, project_binary_name)
            if not os.path.exists(result_dir):
                try:
                    os.makedirs(result_dir)
                except:
                    pass

            result_file = os.path.join(result_dir, os.path.basename(mapping_file1.replace("_function_mapping.json", ""))
                                       + "+" + os.path.basename(mapping_file2).replace("_function_mapping.json",
                                                                                       "") + ".json")
            write_json(result_file, anchor_info)


def evaluate_community_similarities_dispatcher(binary_name_to_fcg_communities):
    cmd_list = []
    for project_binary_name in binary_name_to_fcg_communities:
        cmd_list.append([project_binary_name, binary_name_to_fcg_communities[project_binary_name]])
    print("running evaluation")
    process_num = 12
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(evaluate_community_similarities, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def main():
    results_folder = r"/data1/jiaang/binkit2/9.apply_classifier_to_fcg_nodes/results"
    binary_fcg_labels = get_binary_fcg_labels(results_folder)
    FCG_path = r"/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    binary_name_to_fcg_communities_file = "binary_name_to_fcg_communities.json"
    running_time_file = "running_time.json"

    if not os.path.exists(binary_name_to_fcg_communities_file) or not os.path.exists(running_time_file):
        binary_name_to_fcg_communities, running_time = traverse_fcg_files(FCG_path, binary_fcg_labels)
        write_json(running_time_file, running_time)
        write_json(binary_name_to_fcg_communities_file, binary_name_to_fcg_communities)
    else:
        binary_name_to_fcg_communities = read_json(binary_name_to_fcg_communities_file)
    # evaluate_community_similarities_dispatcher(binary_name_to_fcg_communities)


if __name__ == '__main__':
    main()
