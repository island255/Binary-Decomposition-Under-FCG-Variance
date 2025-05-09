# encoding=utf-8
import json
import os
import pickle
import time
from multiprocessing import Pool
import evaluate_utils
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
                    binary_name = project_binary_name[splitter_position[0] + 1:].replace("_x86_64", "")
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


# def extract_anchor_nodes(binary_fcg, binary_fcg_func_labels):
#     normal_nodes = []
#     for func_name in binary_fcg_func_labels:
#         if not binary_fcg_func_labels[func_name]:
#             normal_nodes.append(func_name)
#     anchor_nodes = list(set(binary_fcg.nodes()).difference(set(normal_nodes)))
#     return anchor_nodes

def extract_anchor_nodes(binary_fcg, binary_fcg_func_labels):
    anchor_nodes = []
    for func_name in binary_fcg_func_labels:
        if binary_fcg_func_labels[func_name]:
            anchor_nodes.append(func_name)
    return anchor_nodes


def examine_node_label_numbers(binary_fcg, binary_fcg_func_labels):
    print('number of nodes', binary_fcg.number_of_nodes())
    print('number of predicted labels', len(list(binary_fcg_func_labels.keys())))


def extract_anchor_communities(binary_fcg_path, binary_fcg_func_labels):
    binary_fcg = read_pickle(binary_fcg_path)
    anchor_nodes = extract_anchor_nodes(binary_fcg, binary_fcg_func_labels)
    # examine_node_label_numbers(binary_fcg, binary_fcg_func_labels)
    anchor_community = traverse_from_common_nodes(binary_fcg, anchor_nodes)
    return anchor_community


def extract_binary_name_from_fcg_file_name(binary_fcg_path):
    binary_fcg_name = os.path.basename(binary_fcg_path)
    binary_name = binary_fcg_name.replace(".i64.fcg.fcg_pkl", "").split("_")[-1]
    opt = "_".join(binary_fcg_name.replace(".i64.fcg.fcg_pkl", "").split("_")[1:-1])
    return binary_name, opt


def traverse_fcg_files(FCG_path, binary_fcg_labels):
    running_time = []
    binary_name_to_fcg_communities = {}
    for project_name in binary_fcg_labels:
        print("processing project {}, use anchor to divide fcgs ...".format(project_name))
        fcg_project_folder = os.path.join(FCG_path, project_name)
        for binary_fcg_name in tqdm(os.listdir(fcg_project_folder)):
            if not binary_fcg_name.endswith(".fcg_pkl"):
                continue
            binary_fcg_path = os.path.join(fcg_project_folder, binary_fcg_name)
            binary_name, opt = extract_binary_name_from_fcg_file_name(binary_fcg_path)
            # print(binary_name, opt)
            if binary_name not in binary_fcg_labels[project_name] or opt not in binary_fcg_labels[project_name][
                binary_name]:
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


def extract_compiler_info(filename):
    """从文件名中提取编译器信息"""
    parts = filename.split('_')
    compiler = None
    version = None
    opt_level = None

    for part in parts:
        if part.startswith('gcc'):
            compiler = 'gcc'
            version = part[4:]
        elif part.startswith('clang'):
            compiler = 'clang'
            version = part[6:]
        elif part in ['O0', 'O1', 'O2', 'O3', 'Ofast', 'Os']:
            opt_level = part

    return compiler, version, opt_level


def is_target_comparison(file1, file2):
    """检查是否为目标比较组合"""
    comp1, ver1, opt1 = extract_compiler_info(file1)
    comp2, ver2, opt2 = extract_compiler_info(file2)

    # 定义目标比较组合
    target_combinations = [
        ('gcc-11.2.0', 'Ofast', 'clang-6.0', 'O0'),
        ('gcc-11.2.0', 'Ofast', 'clang-7.0', 'O0'),
        ('gcc-11.2.0', 'Ofast', 'clang-4.0', 'O0'),
        ('gcc-11.2.0', 'Ofast', 'clang-5.0', 'O0'),
        ('gcc-11.2.0', 'O3', 'clang-6.0', 'O0'),
        ('gcc-11.2.0', 'O3', 'clang-7.0', 'O0'),
        ('gcc-11.2.0', 'O3', 'clang-4.0', 'O0'),
        ('gcc-11.2.0', 'O3', 'clang-5.0', 'O0'),
        ('gcc-6.5.0', 'Ofast', 'clang-4.0', 'O0'),
        ('gcc-6.5.0', 'Ofast', 'clang-6.0', 'O0'),

        ('gcc-7.3.0', 'Ofast', 'clang-8.0', 'O0'),
        ('gcc-7.3.0', 'Ofast', 'clang-9.0', 'O0'),
        ('gcc-7.3.0', 'O3', 'clang-8.0', 'O0'),
        ('gcc-7.3.0', 'O3', 'clang-9.0', 'O0'),
        ('gcc-7.3.0', 'Ofast', 'clang-10.0', 'O0'),
        ('gcc-7.3.0', 'Ofast', 'clang-11.0', 'O0'),
        ('gcc-7.3.0', 'O3', 'clang-10.0', 'O0'),
        ('gcc-7.3.0', 'O3', 'clang-11.0', 'O0'),
        ('gcc-4.9.4', 'Ofast', 'clang-8.0', 'O0'),
        ('gcc-4.9.4', 'Ofast', 'clang-9.0', 'O0')
    ]

    combo1 = (f"{comp1}-{ver1}", opt1, f"{comp2}-{ver2}", opt2)
    combo2 = (f"{comp2}-{ver2}", opt2, f"{comp1}-{ver1}", opt1)

    return combo1 in target_combinations or combo2 in target_combinations


def run_N2NMatcher_evaluation(cmd):
    """执行N2NMatcher评估"""
    project_binary_name, binary_fcg_to_communities = cmd
    results_folder = r"/data1/jiaang/binkit2/9.apply_classifier_to_fcg_nodes/top20//evaluate_results"
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

            if not is_target_comparison(os.path.basename(fcg_file1).replace(".i64.fcg.fcg_pkl", ""),
                                        os.path.basename(fcg_file2).replace(".i64.fcg.fcg_pkl", "")):
                continue

            mapping_file1 = get_mapping_file(fcg_file1, mapping_folder)
            mapping_file2 = get_mapping_file(fcg_file2, mapping_folder)
            mapping1 = read_json(mapping_file1)
            mapping2 = read_json(mapping_file2)

            result_dir = os.path.join(results_folder, project_binary_name)
            result_file = (
                os.path.join(result_dir,
                             os.path.basename(mapping_file1.replace("_function_mapping.json", ""))
                             + "+" + os.path.basename(mapping_file2).replace("_function_mapping.json",
                                                                             "") + ".json"))
            if os.path.exists(result_file):
                continue

            cluster_to_cluster_mappings = evaluate_utils.evaluate_generated_clusters(
                community1, community2, mapping1, mapping2)
            cluster_mapping_statistics = evaluate_utils.summarize_mapping_statistics(
                cluster_to_cluster_mappings)

            anchor_info = {"statistics": cluster_mapping_statistics}


            if not os.path.exists(result_dir):
                try:
                    os.makedirs(result_dir)
                except:
                    pass

            write_json(result_file, anchor_info)


def evaluate_community_similarities_dispatcher(binary_name_to_fcg_communities):
    cmd_list = []
    for project_binary_name in binary_name_to_fcg_communities:
        cmd_list.append([project_binary_name, binary_name_to_fcg_communities[project_binary_name]])
    print("running evaluation")
    process_num = 12
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_N2NMatcher_evaluation, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def main():
    results_folder = r"/data1/jiaang/binkit2/9.apply_classifier_to_fcg_nodes/top20/results/"
    binary_fcg_labels = get_binary_fcg_labels(results_folder)
    FCG_path = r"/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    binary_name_to_fcg_communities_file = "binary_name_to_fcg_communities.json"
    running_time_file = "N2NMatcher_running_time.json"

    if not os.path.exists(binary_name_to_fcg_communities_file) or not os.path.exists(running_time_file):
        binary_name_to_fcg_communities, running_time = traverse_fcg_files(FCG_path, binary_fcg_labels)
        write_json(running_time_file, running_time)
        write_json(binary_name_to_fcg_communities_file, binary_name_to_fcg_communities)
    else:
        binary_name_to_fcg_communities = read_json(binary_name_to_fcg_communities_file)
    evaluate_community_similarities_dispatcher(binary_name_to_fcg_communities)


if __name__ == '__main__':
    main()
