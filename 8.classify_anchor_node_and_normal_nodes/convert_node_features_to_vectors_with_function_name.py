import csv
import os
import json
import tqdm


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)



def convert_bb_mnems_to_vectors(bb_mnems, mnems_list):
    bb_mnems_vec = [0]*len(mnems_list)
    for bb_m in bb_mnems:
        bb_index = mnems_list.index(bb_m)
        bb_mnems_vec[bb_index] += 1
    return bb_mnems_vec


def convert_json_to_csv(project_name, binary_name, features_content, mnems_list):
    features_csv = []
    for opt in features_content:
        for node_type in features_content[opt]:
            for function_name in features_content[opt][node_type]:
                function_features = features_content[opt][node_type][function_name]
                bb_num = function_features["bb_num"]
                function_volume = function_features["function_volume"]
                bb_mnems = function_features["bb_mnems"]
                in_degree = function_features["in_degree"]
                out_degree = function_features["out_degree"]
                successors = function_features["successors"]
                predecessors = function_features["predecessors"]
                bb_mnems_vec = convert_bb_mnems_to_vectors(bb_mnems, mnems_list)
                if node_type == "normal":
                    node_label = 0
                else:
                    node_label = 1
                node_csv_line = [project_name, binary_name, opt, function_name, bb_num, function_volume] + bb_mnems_vec + \
                                [in_degree, out_degree, successors, predecessors, node_label]
                features_csv.append(node_csv_line)
    return features_csv


def summarize_mnem_list(anchor_features_folder):
    mnems_list = []
    for project_binary_name in os.listdir(anchor_features_folder):
        features_file_path = os.path.join(anchor_features_folder, project_binary_name)
        try:
            features_content = read_json(features_file_path)
        except:
            print(features_file_path)
            continue
        for opt in features_content:
            for node_type in features_content[opt]:
                for function_name in features_content[opt][node_type]:
                    bb_mnems = features_content[opt][node_type][function_name]["bb_mnems"]
                    mnems_list = set(mnems_list).union(set(bb_mnems))
    return list(mnems_list)


def write_csv(csv_file_path, features_csv):
    csv_writer = csv.writer(open(csv_file_path, "w", newline=""))
    for line in features_csv:
        csv_writer.writerow(line)


def traverse_node_features_files():
    arch_list = ['x86_32', 'x86_64', 'arm_32', 'arm_64', 'mipseb_32', 'mipseb_64']
    for arch in arch_list:
        anchor_features_folder = r"/data1/jiaang/binkit2/8.classify_anchor_node_and_normal_nodes/anchor_features_by_arch/" + arch
        csv_file_path = r"/data1/jiaang/binkit2/8.classify_anchor_node_and_normal_nodes/node_features_with_function_name_csv_" + arch + ".csv"
        if os.path.exists(csv_file_path):
            continue
        mnems_list_file = "mnems_list_" + arch + ".json"
        if not os.path.exists(mnems_list_file):
            mnems_list = summarize_mnem_list(anchor_features_folder)
            write_json(mnems_list_file, mnems_list)
        else:
            mnems_list = read_json(mnems_list_file)

        csv_first_line = ["project_name", "binary_name", "opt", "function_name", "bb_num", "function_volume"] + mnems_list + \
                         ["in_degree", "out_degree", "successors", "predecessors", "node_label"]
        all_features_csv = [csv_first_line]
        # csv_folder = r"/data1/jiaang/binkit2/8.classify_anchor_node_and_normal_nodes/csv"
        for project_binary_name in tqdm.tqdm(os.listdir(anchor_features_folder)):
            project_name, binary_name = project_binary_name.split("+")[0], project_binary_name.replace(".json", "")
            features_file_path = os.path.join(anchor_features_folder, project_binary_name)
            features_content = read_json(features_file_path)
            features_csv = convert_json_to_csv(project_name, binary_name, features_content, mnems_list)
            all_features_csv += features_csv
        # csv_file_path = os.path.join(csv_folder, project_binary_name.replace(".json", ".csv"))
        write_csv(csv_file_path, all_features_csv)


if __name__ == '__main__':
    traverse_node_features_files()