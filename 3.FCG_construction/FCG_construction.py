import json
import os
import pickle
import networkx as nx
from tqdm import tqdm
from multiprocessing import Pool


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)


def write_pickle(obj, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(obj, f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def read_binary_list(projectdir):
    """
    get all binary file's path
    """
    binary_paths = []
    for root, dirs, files in os.walk(projectdir):
        for file_name in files:
            if file_name.endswith(".fcg"):
                file_path = os.path.join(root, file_name)
                binary_paths.append(file_path)
    return binary_paths


def extract_address_to_name_mapping(binary_range):
    binary_function_start_address_to_function_name = {}
    for function_name in binary_range:
        start_address = binary_range[function_name]["start_address"]
        binary_function_start_address_to_function_name[start_address] = function_name
    return binary_function_start_address_to_function_name


def construct_fcg_for_binary(binary_range_file, binary_FCG_file):
    binary_range = read_json(binary_range_file)
    binary_function_start_address_to_function_name = extract_address_to_name_mapping(binary_range)
    binary_FCG_call_pairs = read_json(binary_FCG_file)
    binary_FCG = nx.MultiDiGraph()
    for call_pair in binary_FCG_call_pairs:
        caller_function_address, callee_function_address, call_location = call_pair
        caller_function_address = int(caller_function_address, 16)
        callee_function_address = int(callee_function_address, 16)
        caller_function_name = binary_function_start_address_to_function_name[caller_function_address]
        callee_function_name = binary_function_start_address_to_function_name[callee_function_address]
        if caller_function_name not in binary_FCG:
            binary_FCG.add_node(caller_function_name, node_attribute=binary_range[caller_function_name])
        if callee_function_name not in binary_FCG:
            binary_FCG.add_node(callee_function_name, node_attribute=binary_range[callee_function_name])
        binary_FCG.add_edge(caller_function_name, callee_function_name, call_site_location=call_location)
    return binary_FCG


def extract_function_mapping(binary_range_file):
    binary_address_name_to_function_name_mapping = {}
    binary_function_range = read_json(binary_range_file)
    for function_name in binary_function_range:
        function_start_address_in_10 = binary_function_range[function_name]["start_address"]
        function_address_name = "Func_00" + str(hex(function_start_address_in_10))[2:]
        binary_address_name_to_function_name_mapping[function_address_name] = function_name
    return binary_address_name_to_function_name_mapping


def construct_fcg(binary_path):
    binary_project_folder = r"/data1/jiaang/binkit2/2.IDA_FCG_extraction/FCG_dataset_I"
    dest_pkl_dir = r"/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"

    dest_binary_mapping_file = binary_path.replace(binary_project_folder, dest_pkl_dir) + ".mapping"
    dest_fcg_file = binary_path.replace(binary_project_folder, dest_pkl_dir) + ".fcg_pkl"

    if os.path.exists(dest_binary_mapping_file) and os.path.exists(dest_fcg_file):
        return

    binary_range_file = binary_path.replace(".fcg", ".json")
    binary_FCG_file = binary_path
    elf_name = os.path.basename(binary_path)
    binary_address_name_to_function_name_mapping = extract_function_mapping(binary_range_file)
    binary_fcg = construct_fcg_for_binary(binary_range_file, binary_FCG_file)

    if not os.path.exists(os.path.dirname(dest_fcg_file)):
        try:
            os.makedirs(os.path.dirname(dest_fcg_file))
        except:
            pass
    write_json(dest_binary_mapping_file, binary_address_name_to_function_name_mapping)
    write_pickle(binary_fcg, dest_fcg_file)


def main():
    binary_project_folder = r"/data1/jiaang/binkit2/2.IDA_FCG_extraction/FCG_dataset_I"
    dest_pkl_dir = r"/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    project_name_list = os.listdir(binary_project_folder)
    binary_paths_list = []
    for project_name in project_name_list:
        binary_project_dir = os.path.join(binary_project_folder, project_name)
        binary_paths = read_binary_list(binary_project_dir)
        binary_paths_list += binary_paths

    process_num = 16
    p = Pool(int(process_num))
    with tqdm(total=len(binary_paths_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(construct_fcg, binary_paths_list))):
            pbar.update()
    p.close()
    p.join()


if __name__ == '__main__':
    main()
