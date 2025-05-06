import json
import os


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def add_statistics(normal_statistics, result_dict):
    for number in result_dict:
        if number not in normal_statistics:
            normal_statistics[number] = []
        normal_statistics[number] += result_dict[number]
    return normal_statistics


def summarize_cluster_statistics():
    evaluate_method = "N2NMatcher"
    ModX_evaluate_results_dir = r"/data1/jiaang/binkit2/9.apply_classifier_to_fcg_nodes/evaluate_results_new/"
    normal_statistics = {}
    inlining_statistics = {}
    for binary_name in os.listdir(ModX_evaluate_results_dir):
        binary_dir = os.path.join(ModX_evaluate_results_dir, binary_name)
        for result_file in os.listdir(binary_dir):
            result_file_path = os.path.join(binary_dir, result_file)
            result = read_json(result_file_path)
            normal_statistics = add_statistics(normal_statistics, result["statistics"]["normal"])
            inlining_statistics = add_statistics(inlining_statistics, result["statistics"]["inlining"])
    write_json(evaluate_method + "_normal_statistics.json", normal_statistics)
    write_json(evaluate_method + "_inlining_statistics.json", inlining_statistics)


if __name__ == '__main__':
    summarize_cluster_statistics()