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


def summarize_community_size_dispatcher(cmd_list):
    print("comparing communities...")
    process_num = 16
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(summarize_community_size, cmd_list))):
            pbar.update()
    p.close()
    p.join()






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


def extract_cluster_size(cluster):
    cluster_size_distribution = {}
    for community in cluster:
        size = len(community)
        if size not in cluster_size_distribution:
            cluster_size_distribution[size] = 0
        cluster_size_distribution[size] += 1
    return cluster_size_distribution


def summarize_community_size(cmd):
    binary_name, cluster_file, result_folder, evaluate_method = cmd
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
    cluster_size_distribution = extract_cluster_size(cluster)
    write_json(modx_result_path, cluster_size_distribution)


def generate_cmds_for_evaluation(cluster_files, result_folder, evaluate_method):
    cmd_list = []
    for binary_name in cluster_files:
        binary_to_cluster_files = cluster_files[binary_name]
        for cluster_file in binary_to_cluster_files:
            cmd_list.append([binary_name, cluster_file, result_folder, evaluate_method])
    return cmd_list


def generate_size_summary(result_folder):
    cluster_size_distribution = {}
    for project_binary_name in os.listdir(result_folder):
        project_folder = os.path.join(result_folder, project_binary_name)
        for binary_size_file in os.listdir(project_folder):
            binary_size_file_path = os.path.join(project_folder, binary_size_file)
            binary_size_content = read_json(binary_size_file_path)
            if not cluster_size_distribution:
                cluster_size_distribution = binary_size_content
            else:
                for key in binary_size_content:
                    if key not in cluster_size_distribution:
                        cluster_size_distribution[key] = binary_size_content[key]
                    else:
                        cluster_size_distribution[key] += binary_size_content[key]
    return cluster_size_distribution


def main():
    arch = "x86_64"

    evaluate_method_list = ["ModX", "BMVul"]
    for evaluate_method in evaluate_method_list:
        method_results_folder = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/" + evaluate_method + "/results/"
        result_folder = r"/data1/jiaang/binkit2/7.anchor_node_labeling/using_anchor_to_evaluate_existing_works/" + evaluate_method + "/size"
        if evaluate_method == "ModX":
            cluster_files = get_ModX_cluster_files(method_results_folder, arch)
        elif evaluate_method == "BMVul":
            cluster_files = get_BMVul_cluster_files(method_results_folder, arch)
        cmd_list = generate_cmds_for_evaluation(cluster_files, result_folder, evaluate_method)
        summarize_community_size_dispatcher(cmd_list)

        size_summary_file = evaluate_method + "_size_summary.json"
        size_summary = generate_size_summary(result_folder)
        write_json(size_summary_file, size_summary)

if __name__ == '__main__':
    main()