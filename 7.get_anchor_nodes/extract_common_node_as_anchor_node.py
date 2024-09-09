import json
import os


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def merge_list(common_node_list):
    merged_anchor_node = set(common_node_list[0])
    for common_node in common_node_list:
        merged_anchor_node = set(merged_anchor_node).intersection(set(common_node))
    return list(merged_anchor_node)


def main():
    anchor_dir = r"/data1/jiaang/binkit2/7.anchor_node_identification/anchor"
    result_dir = r"/data1/jiaang/binkit2/7.anchor_node_identification/merged_anchor"
    for binary_name in os.listdir(anchor_dir):
        binary_dir = os.path.join(anchor_dir, binary_name)
        result_folder = os.path.join(result_dir, binary_name)
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        common_node_list = []
        for anchor_file in os.listdir(binary_dir):
            result_file_path = os.path.join(binary_dir, anchor_file)
            result = read_json(result_file_path)
            anchor_node = result["anchor_node"]
            common_node_list.append(anchor_node)
        merged_anchor_node = merge_list(common_node_list)
        result_file_path = os.path.join(result_folder, binary_name + ".json")
        write_json(result_file_path, merged_anchor_node)


if __name__ == '__main__':
    main()