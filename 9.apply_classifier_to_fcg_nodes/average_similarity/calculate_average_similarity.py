import json
import os

from tqdm import tqdm


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


def calculate_avg_similarity_N2NMatcher(ModX_evaluate_results_dir):
    similarity = []
    for binary_name in tqdm(os.listdir(ModX_evaluate_results_dir)):
        binary_dir = os.path.join(ModX_evaluate_results_dir, binary_name)
        for result_file in os.listdir(binary_dir):
            result_file_path = os.path.join(binary_dir, result_file)
            result = read_json(result_file_path)
            for func_type in result["statistics"]:
                for number in result["statistics"][func_type]:
                    similarity += result["statistics"][func_type][number]
    final_similarity = sum(similarity) / len(similarity)
    print(final_similarity)

def calculate_avg_similarity(ModX_evaluate_results_dir):
    similarity = []
    for binary_name in tqdm(os.listdir(ModX_evaluate_results_dir)):
        binary_dir = os.path.join(ModX_evaluate_results_dir, binary_name)
        for result_file in os.listdir(binary_dir):
            result_file_path = os.path.join(binary_dir, result_file)
            result = read_json(result_file_path)
            for func_type in result:
                for number in result[func_type]:
                    similarity += result[func_type][number]
    final_similarity = sum(similarity) / len(similarity)
    print(final_similarity)


def summarize_cluster_statistics():
    print("N2NMatcher:")
    N2NMatcher_evaluate_results_dir = r"D:\binkit2\code\9.apply_classifier_to_fcg_nodes/evaluate_results_new"
    calculate_avg_similarity_N2NMatcher(N2NMatcher_evaluate_results_dir)
    print("ModX:")
    ModX_evaluate_results_dir = r"D:\binkit2\code\6.evaluate_existing_work\ModX\results"
    calculate_avg_similarity(ModX_evaluate_results_dir)
    print("BMVul:")
    BMVul_evaluate_results_dir = r"D:\binkit2\code\6.evaluate_existing_work\BMVul\results"
    calculate_avg_similarity(BMVul_evaluate_results_dir)


if __name__ == '__main__':
    summarize_cluster_statistics()