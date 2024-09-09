import json
import os
import pickle
import tqdm


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)



def test():
    pkl_file = r"D:\binkit2\code\3.FCG_construction\pkl_example\a2ps-4.14_clang-4.0_arm_32_O0_a2ps.i64.fcg.fcg_pkl"
    pkl_content = read_pickle(pkl_file)
    print("debug")


def read_binary_list(projectdir):
    """
    get all binary file's path
    """
    binary_paths = []
    for root, dirs, files in os.walk(projectdir):
        for file_name in files:
            if file_name.endswith(".fcg_pkl"):
                file_path = os.path.join(root, file_name)
                binary_paths.append(file_path)
    return binary_paths


def get_split_parts(elf_name):
    _, compiler, arch1, arch2, opt = elf_name.split("_")[:5]
    return compiler, arch1 + "_" + arch2, opt


def main():
    fcg_pkl_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    project_name_list = os.listdir(fcg_pkl_folder)
    binary_fcg_paths_list = []
    for project_name in project_name_list:
        binary_project_dir = os.path.join(fcg_pkl_folder, project_name)
        binary_fcg_paths = read_binary_list(binary_project_dir)
        binary_fcg_paths_list += binary_fcg_paths

    summary_for_fcg = {}
    for binary_fcg_path in tqdm.tqdm(binary_fcg_paths_list):
        fcg_content = read_pickle(binary_fcg_path)
        node_num = fcg_content.number_of_nodes()
        edge_num = fcg_content.number_of_edges()
        elf_name = os.path.basename(binary_fcg_path)
        compiler, arch, opt = get_split_parts(elf_name)
        if arch not in summary_for_fcg:
            summary_for_fcg[arch] = {}
        if compiler not in summary_for_fcg[arch]:
            summary_for_fcg[arch][compiler] = {}
        if opt not in summary_for_fcg[arch][compiler]:
            summary_for_fcg[arch][compiler][opt] = {"nodes":[], "edges":[]}
        summary_for_fcg[arch][compiler][opt]["nodes"].append(node_num)
        summary_for_fcg[arch][compiler][opt]["edges"].append(edge_num)

    summary_for_fcg_file = "summary_for_fcg.json"
    write_json(summary_for_fcg_file, summary_for_fcg)



if __name__ == '__main__':
    # test()
    main()
