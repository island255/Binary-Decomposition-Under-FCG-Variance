from argparse import Namespace
import oslom


def run_oslom_using_args():
    # run OSLOM with files already on disk
    args = Namespace()
    args.edges = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\example.dat"
    args.output_clusters = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\output_clusters.json"
    args.oslom_output = r"D:\binkit2\code\5.implement_strategy_of_existing_works\BMVUL\test\oslom_aux_files"
    args.min_cluster_size = oslom.DEF_MIN_CLUSTER_SIZE
    args.oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_undir.exe"
    args.oslom_args = ["-uw", "-r", "10", "-hr", "10"]
    oslom.run(args)


def run_oslom_in_py():
    # run OSLOM with data in Python objects
    args = Namespace()
    args.min_cluster_size = 0
    args.oslom_exec = r"D:\binkit2\related_work\OSLOM2\oslom_undir.exe"
    args.oslom_args = oslom.DEF_OSLOM_ARGS

    # edges is an iterable of tuples (source, target, weight)
    # in the same format as the command-line version
    edges = [(0, 1, 1.0), (1, 2, 1), (2, 0, 1)]
    clusters = oslom.run_in_memory(args, edges)
    print(clusters)


if __name__ == '__main__':
    run_oslom_using_args()
    run_oslom_in_py()
