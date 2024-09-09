import json
import os
import pickle
import subprocess
from multiprocessing import Pool

from tqdm import tqdm


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def construct_CG(FCG):
    CG_edges_with_weight = {}
    all_edges = list(FCG.edges())
    for edge in all_edges:
        if edge not in CG_edges_with_weight:
            CG_edges_with_weight[edge] = 0
        CG_edges_with_weight[edge] += 1
    # FCG_with_weight = nx.DiGraph()
    all_nodes = list(FCG.nodes())
    edge_with_weights = []
    for edge in CG_edges_with_weight:
        # FCG_with_weight.add_edge(edge[0], edge[1], weight=CG_edges_with_weight[edge])
        # edge_with_weights.append((all_nodes.index(edge[0]), all_nodes.index(edge[1]), CG_edges_with_weight[edge]))
        edge_with_weights.append((edge[0], edge[1], CG_edges_with_weight[edge]))
    return edge_with_weights


def write_edge_file(edge_with_weights, test_file_path):
    with open(test_file_path, "w") as f:
        for edge in edge_with_weights:
            edge = [str(item) for item in edge]
            f.write("\t".join(edge) + "\n")


def generate_edge_file(args):
    edge_project_folder, fcg_file_path = args
    dest_edge_file_path = os.path.join(edge_project_folder, os.path.basename(fcg_file_path) + ".tsv")
    if os.path.exists(dest_edge_file_path):
        return
    fcg = read_pickle(fcg_file_path)
    edge_with_weights = construct_CG(fcg)
    write_edge_file(edge_with_weights, dest_edge_file_path)


def generate_edge_file_dispatcher(edge_cmd_list):
    print("generate edge file")
    process_num = 12
    p = Pool(int(process_num))
    with tqdm(total=len(edge_cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(generate_edge_file, edge_cmd_list))):
            pbar.update()
    p.close()
    p.join()


def generate_cmd_list(edge_file_list):
    cmd_list = []
    result_dir = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/BMVul/results"
    for edge_file_path in edge_file_list:
        project_name = os.path.basename(os.path.dirname(edge_file_path))
        file_name = os.path.basename(edge_file_path)[:-4]
        dest_result_path = os.path.join(result_dir, project_name, file_name)
        if not os.path.exists(dest_result_path):
            os.makedirs(dest_result_path)

        clusters = os.path.join(dest_result_path, "clusters.json")
        oslom_output = os.path.join(dest_result_path, "oslom_output")
        oslom_exec = r"/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/BMVul/OSLOM2/oslom_dir"
        oslom_runner = r"/home/jiaang/.conda/envs/fcg_analysis_py27/bin/oslom-runner"
        if os.path.exists(clusters):
            continue
        args = [oslom_runner, "--edges", edge_file_path,
                "--output-clusters", clusters, "--oslom-output", oslom_output,
                "--oslom-exec", oslom_exec]
        cmd_list.append(args)
    return cmd_list


def run_script_in_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    # print(stdout, stderr)


def run_BMVul_on_Binkit(edge_file_list):
    cmd_list = generate_cmd_list(edge_file_list)
    print("running OSLOM")
    process_num = 12
    p = Pool(int(process_num))
    with tqdm(total=len(cmd_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_script_in_cmd, cmd_list))):
            pbar.update()
    p.close()
    p.join()


def main():
    FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    edge_cmd_list = []
    fcg_edge_folder = "/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/BMVul/edge_list"
    edge_file_list = []
    project_name_list = os.listdir(FCG_folder)
    for project_name in project_name_list:
        project_dir = os.path.join(FCG_folder, project_name)
        edge_project_folder = os.path.join(fcg_edge_folder, project_name)
        if not os.path.exists(edge_project_folder):
            os.makedirs(edge_project_folder)

        for fcg_file_name in os.listdir(project_dir):
            if not fcg_file_name.endswith(".fcg_pkl"):
                continue
            dest_edge_file_path = os.path.join(edge_project_folder, fcg_file_name + ".tsv")
            edge_file_list.append(dest_edge_file_path)
            if os.path.exists(dest_edge_file_path):
                continue
            fcg_file_path = os.path.join(project_dir, fcg_file_name)
            edge_cmd_list.append([edge_project_folder, fcg_file_path])

    generate_edge_file_dispatcher(edge_cmd_list)

    run_BMVul_on_Binkit(edge_file_list)


if __name__ == '__main__':
    main()
