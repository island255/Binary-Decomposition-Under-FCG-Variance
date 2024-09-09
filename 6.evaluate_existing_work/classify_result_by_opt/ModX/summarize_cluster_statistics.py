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


def analyze_opt(result_file):
    if "c++" in result_file:
        result_file = result_file.replace("c++", "cxx")
    binary_name1 = result_file.split("+")[0]
    binary_name2 = result_file.split("+")[1]
    opt1 = binary_name1.split("_")[4]
    opt2 = binary_name2.split("_")[4]
    return opt1, opt2


def summarize_cluster_statistics():
    evaluate_method = "ModX"
    ModX_evaluate_results_dir = r"/data1/jiaang/binkit2/6.evaluate_existing_work/"+ evaluate_method + "/results"
    opt2opt_statistics = {}
    for binary_name in os.listdir(ModX_evaluate_results_dir):
        binary_dir = os.path.join(ModX_evaluate_results_dir, binary_name)
        for result_file in os.listdir(binary_dir):
            opt1, opt2 = analyze_opt(result_file)
            result_file_path = os.path.join(binary_dir, result_file)
            result = read_json(result_file_path)
            if opt1 not in opt2opt_statistics:
                opt2opt_statistics[opt1] = {}
            if opt2 not in opt2opt_statistics[opt1]:
                opt2opt_statistics[opt1][opt2] = {}
            opt2opt_statistics[opt1][opt2] = add_statistics(opt2opt_statistics[opt1][opt2], result)
    write_json(evaluate_method + "_opt2opt_statistics.json", opt2opt_statistics)


if __name__ == '__main__':
    summarize_cluster_statistics()