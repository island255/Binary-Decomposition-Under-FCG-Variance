#encoding=utf-8
import json
import os
import pickle
from multiprocessing import Pool

import networkx as nx
# from matplotlib import pyplot as plt
from tqdm import tqdm
import sys
import evaluate_utils
import time


def extract_clusters(O0_cluster_content):
    O0_cluster = []
    for community_dict in O0_cluster_content:
        community_nodes_dict = community_dict["nodes"]
        community_nodes = []
        for node_dict in community_nodes_dict:
            function_name = node_dict["id"]
            community_nodes.append(function_name)
        O0_cluster.append(community_nodes)
    return O0_cluster


def get_cluster_files(BMVul_results_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(BMVul_results_folder):
        project_folder = os.path.join(BMVul_results_folder, project_name)
        for binary_pkl in os.listdir(project_folder):
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


def generate_cmds(cluster_files, fcg_folder, result_folder, comparison_type="cross_compiler"):
    cmd_list = []
    for binary_name in cluster_files:
        binary_to_cluster_files = cluster_files[binary_name]
        cmd_list.append([binary_name, binary_to_cluster_files, fcg_folder, result_folder, comparison_type])
    return cmd_list


def get_mapping_file(cluster_file1, mapping_folder):
    binary_fcg_pkl_name1 = os.path.basename(os.path.dirname(cluster_file1)).replace(".i64.fcg.fcg_pkl",
                                                                                    "_function_mapping.json")
    binary_project_name1 = os.path.basename(os.path.dirname(os.path.dirname(cluster_file1)))
    mapping_file1 = os.path.join(mapping_folder, binary_project_name1, binary_fcg_pkl_name1)
    return mapping_file1


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


def extract_comparison_settings(top10_root_mapping):
    target_combinations = []
    for comparison_dict in top10_root_mapping["top_10"]:
        comparison = comparison_dict["comparison"]
        compiler_opt_1, compiler_opt_2 = comparison.split(" vs ")
        compiler1, opt1 = compiler_opt_1.split("_")[2], compiler_opt_1.split("_")[3]
        compiler2, opt2 = compiler_opt_2.split("_")[0], compiler_opt_2.split("_")[1]
        target_combinations.append((compiler1, opt1, compiler2, opt2))
    return target_combinations


def read_from_mapping_files(top10_relevant_mapping_file, top10_root_mapping_file):
    top10_root_mapping = evaluate_utils.read_json(top10_root_mapping_file)
    top10_relevant_mapping = evaluate_utils.read_json(top10_relevant_mapping_file)
    top10_root_comparison = extract_comparison_settings(top10_root_mapping)
    top10_relevant_comparisons = extract_comparison_settings(top10_relevant_mapping)
    return top10_root_comparison + top10_relevant_comparisons


def is_target_comparison(file1, file2):
    """检查是否为目标比较组合"""
    comp1, ver1, opt1 = extract_compiler_info(file1)
    comp2, ver2, opt2 = extract_compiler_info(file2)

    top10_relevant_mapping_file = "top10_relevant.json"
    top10_root_mapping_file = "top10_root_equivalent.json"
    # 定义目标比较组合
    # target_combinations = [
    #     ('gcc-11.2.0', 'Ofast', 'clang-6.0', 'O0'),
    #     ('gcc-11.2.0', 'Ofast', 'clang-7.0', 'O0'),
    # ]

    target_combinations = read_from_mapping_files(top10_relevant_mapping_file, top10_root_mapping_file)
    # print(target_combinations)

    combo1 = (f"{comp1}-{ver1}", opt1, f"{comp2}-{ver2}", opt2)
    combo2 = (f"{comp2}-{ver2}", opt2, f"{comp1}-{ver1}", opt1)

    return combo1 in target_combinations or combo2 in target_combinations


def is_same_compiler_diff_opt(file1, file2):
    """检查是否是同编译器不同优化级别的比较"""
    comp1, ver1, opt1 = extract_compiler_info(file1)
    comp2, ver2, opt2 = extract_compiler_info(file2)

    # 确保是同一个编译器且相同版本
    if comp1 == comp2 and ver1 == ver2:
        # 确保优化级别不同
        if opt1 != opt2:
            return True
    return False


def run_BMVul_evaluation_in_linux(cmd):
    binary_name, binary_to_cluster_files, mapping_folder, result_folder, comparison_type = cmd
    for index1 in range(0, len(binary_to_cluster_files)):
        for index2 in range(0, len(binary_to_cluster_files)):
            if index1 == index2:
                continue

            cluster_file1 = binary_to_cluster_files[index1]
            cluster_file2 = binary_to_cluster_files[index2]

            # 根据比较类型选择不同的比较函数
            if comparison_type == "cross_compiler":
                if not is_target_comparison(os.path.basename(os.path.dirname(cluster_file1)),
                                            os.path.basename(os.path.dirname(cluster_file2))):
                    continue
            elif comparison_type == "same_compiler_diff_opt":
                if not is_same_compiler_diff_opt(os.path.basename(os.path.dirname(cluster_file1)),
                                                 os.path.basename(os.path.dirname(cluster_file2))):
                    continue

            mapping_file1 = get_mapping_file(cluster_file1, mapping_folder)
            mapping_file2 = get_mapping_file(cluster_file2, mapping_folder)

            result_dir = os.path.join(result_folder, binary_name)
            if not os.path.exists(result_dir):
                try:
                    os.makedirs(result_dir)
                except:
                    pass

            result_file = os.path.join(result_dir,
                                       os.path.basename(mapping_file1.replace("_function_mapping", ""))
                                       + "+" + os.path.basename(mapping_file2).replace("_function_mapping",
                                                                                       "") + ".json")
            if os.path.exists(result_file):
                continue


            mapping1 = evaluate_utils.read_json(mapping_file1)
            mapping2 = evaluate_utils.read_json(mapping_file2)

            cluster1_content = evaluate_utils.read_json(cluster_file1)
            cluster1 = extract_clusters(cluster1_content)
            cluster2_content = evaluate_utils.read_json(cluster_file2)
            cluster2 = extract_clusters(cluster2_content)

            cluster_to_cluster_mappings = evaluate_utils.evaluate_generated_clusters(cluster1, cluster2, mapping1,
                                                                                     mapping2)
            cluster_mapping_statistics = evaluate_utils.summarize_mapping_statistics(
                cluster_to_cluster_mappings)

            evaluate_utils.write_json(result_file, cluster_mapping_statistics)


def run_BMVul_evaluation_dispatcher(cmd_list):
    print("running evaluation")
    process_num = 16
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_BMVul_evaluation_in_linux, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def run_BMVul_evaluation(comparison_type="cross_compiler"):
    start_time = time.time()
    arch = "x86_64"
    BMVul_results_folder = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/BMVul/results"
    cluster_files = get_cluster_files(BMVul_results_folder, arch)
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"

    # 根据比较类型设置不同的结果文件夹
    if comparison_type == "cross_compiler":
        result_folder = r"/data1/jiaang/binkit2/6.evaluate_existing_work/BMVul/results_top10"
    else:
        result_folder = r"/data1/jiaang/binkit2/6.evaluate_existing_work/BMVul/results_same_compiler_diff_opt"

    cmd_list = generate_cmds(cluster_files, mapping_folder, result_folder, comparison_type)
    run_BMVul_evaluation_dispatcher(cmd_list)
    end_time = time.time()
    print(end_time - start_time)
    evaluate_utils.write_json(f"BMVul_running_time_{comparison_type}.json", end_time - start_time)


if __name__ == '__main__':
    # 运行跨编译器比较
    run_BMVul_evaluation(comparison_type="cross_compiler")

    # 运行同编译器不同优化级别比较
    run_BMVul_evaluation(comparison_type="same_compiler_diff_opt")