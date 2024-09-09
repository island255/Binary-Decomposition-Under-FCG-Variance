import json
import os.path
import pickle
from argparse import Namespace
import subprocess
import oslom


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
    return edge_with_weights, all_nodes


def run_oslom(edge_with_weights):
    args = Namespace()
    args.min_cluster_size = 0
    args.oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_dir.exe"
    args.oslom_args = oslom.DEF_OSLOM_ARGS

    # edges is an iterable of tuples (source, target, weight)
    # in the same format as the command-line version
    edges = edge_with_weights
    clusters = oslom.run_in_memory(args, edges)
    print(clusters)
    return clusters


def write_edge_file(edge_with_weights, test_file_path):
    with open(test_file_path, "w") as f:
        for edge in edge_with_weights:
            edge = [str(item) for item in edge]
            f.write("\t".join(edge) + "\n")


def run_oslom_in_file(edge_with_weights):
    args = Namespace()
    test_file_path = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\test.tsv"
    write_edge_file(edge_with_weights, test_file_path)
    args.edges = test_file_path
    args.output_clusters = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\output_clusters.json"
    args.oslom_output = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\oslom_aux_files"
    args.min_cluster_size = oslom.DEF_MIN_CLUSTER_SIZE
    args.oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_dir.exe"
    args.oslom_args = ["-w", "-r", "10", "-hr", "10"]
    oslom.run(args)


def run_script_in_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    print(stdout, stderr)


def run_oslom_using_subprocess(edge_with_weights):
    test_file_path = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\test.tsv"
    write_edge_file(edge_with_weights, test_file_path)
    oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_dir.exe"
    oslom_args = ["-w", "-r", "10", "-hr", "10"]
    args = [oslom_exec, "-f", test_file_path] + oslom_args
    print(" ".join(args))
    run_script_in_cmd(args)


def run_oslom_pyrunner(edge_with_weights):
    test_file_path = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\test.tsv"
    write_edge_file(edge_with_weights, test_file_path)
    result_dir = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\results\test"
    clusters = os.path.join(result_dir, "clusters.json")
    oslom_output = os.path.join(result_dir, "oslom_output")
    oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_dir.exe"
    oslom_runner = r"C:\Users\jiaang\anaconda3\envs\fcg_analysis-py27\Scripts\oslom-runner.exe"
    args = [oslom_runner, "--edges", test_file_path,
            "--output-clusters", clusters, "--oslom-output", oslom_output,
            "--oslom-exec", oslom_exec]
    print(" ".join(args))
    run_script_in_cmd(args)


def main():
    FCG_file = r"D:\binkit2\code\5.implement_strategy_of_existing_works\ModX\FCG_pkl\a2ps\a2ps-4.14_clang-4.0_arm_32_O3_a2ps.i64.fcg.fcg_pkl"
    FCG = read_pickle(FCG_file)
    edge_with_weights, all_nodes = construct_CG(FCG)
    # clusters = run_oslom(edge_with_weights)
    # run_oslom_in_file(edge_with_weights)
    # run_oslom_using_subprocess(edge_with_weights)
    run_oslom_pyrunner(edge_with_weights)


if __name__ == '__main__':
    main()
