import json
import os
import pickle
from multiprocessing import Pool

import networkx as nx
from matplotlib import pyplot as plt
from tqdm import tqdm
import sys
import evaluate_utils


def get_cluster_files(ModX_results_folder, arch=None):
    binary_name_to_compilations = {}
    for project_name in os.listdir(ModX_results_folder):
        project_folder = os.path.join(ModX_results_folder, project_name)
        for binary_json in os.listdir(project_folder):
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


def generate_cmds(cluster_files, fcg_folder, result_folder):
    cmd_list = []
    for binary_name in cluster_files:
        binary_to_cluster_files = cluster_files[binary_name]
        cmd_list.append([binary_name, binary_to_cluster_files, fcg_folder, result_folder])
    return cmd_list


def get_mapping_file(cluster_file1, mapping_folder):
    binary_fcg_pkl_name1 = os.path.basename(cluster_file1[:-5]) + "_function_mapping.json"
    binary_project_name1 = os.path.basename(os.path.dirname(cluster_file1))
    mapping_file1 = os.path.join(mapping_folder, binary_project_name1, binary_fcg_pkl_name1)
    return mapping_file1


def run_ModX_evaluation_in_linux(cmd):
    binary_name, binary_to_cluster_files, mapping_folder, result_folder = cmd
    # print(fcg_folder, result_folder)
    for index1 in range(0, len(binary_to_cluster_files)):
        for index2 in range(0, len(binary_to_cluster_files)):
            if index1 == index2:
                continue
            cluster_file1 = binary_to_cluster_files[index1]
            cluster_file2 = binary_to_cluster_files[index2]
            cluster1 = evaluate_utils.read_json(cluster_file1)
            cluster2 = evaluate_utils.read_json(cluster_file2)

            mapping_file1 = get_mapping_file(cluster_file1, mapping_folder)
            mapping_file2 = get_mapping_file(cluster_file2, mapping_folder)
            mapping1 = evaluate_utils.read_json(mapping_file1)
            mapping2 = evaluate_utils.read_json(mapping_file2)

            cluster_to_cluster_mappings = evaluate_utils.evaluate_generated_clusters(cluster1, cluster2, mapping1,
                                                                                     mapping2)
            cluster_mapping_statistics = evaluate_utils.summarize_mapping_statistics(
                cluster_to_cluster_mappings)

            # project_name = os.path.basename(os.path.dirname(os.path.dirname(cluster_file1)))
            result_dir = os.path.join(result_folder, binary_name)
            if not os.path.exists(result_dir):
                try:
                    os.makedirs(result_dir)
                except:
                    pass
            result_file = os.path.join(result_dir, os.path.basename(mapping_file1.replace("_function_mapping.json", ""))
                                       + "+" + os.path.basename(mapping_file2).replace("_function_mapping.json",
                                                                                       "") + ".json")
            evaluate_utils.write_json(result_file, cluster_mapping_statistics)


def run_ModX_evaluation_dispatcher(cmd_list):
    print("running evaluation")
    process_num = 4
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_ModX_evaluation_in_linux, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def run_ModX_evaluation():
    arch = "clang-4.0_x86_64"
    ModX_results_folder = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/ModX/results"
    cluster_files = get_cluster_files(ModX_results_folder, arch)
    mapping_folder = r"/data1/jiaang/binkit2/Dataset/mapping_results"
    result_folder = r"/data1/jiaang/binkit2/6.evaluate_existing_work/ModX/results"
    cmd_list = generate_cmds(cluster_files, mapping_folder, result_folder)
    run_ModX_evaluation_dispatcher(cmd_list)


if __name__ == '__main__':
    # example_test()
    # example_test2()
    run_ModX_evaluation()
