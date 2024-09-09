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
    elf_name = elf_name[:-16]
    project, compiler, arch1, arch2, opt = elf_name.split("_")[:5]
    binary_name = "_".join(elf_name.split("_")[5:])
    return project, compiler, arch1 + "_" + arch2, opt, binary_name


def classify_binaries_by_name(binary_fcg_paths_list):
    binary_to_fcg = {}
    for binary_fcg_path in tqdm.tqdm(binary_fcg_paths_list):
        elf_name = os.path.basename(binary_fcg_path)
        project, compiler, arch, opt, binary_name = get_split_parts(elf_name)
        binary_name = project + "_" + binary_name
        if binary_name not in binary_to_fcg:
            binary_to_fcg[binary_name] = {}
        if arch not in binary_to_fcg[binary_name]:
            binary_to_fcg[binary_name][arch] = {}
        if compiler not in binary_to_fcg[binary_name][arch]:
            binary_to_fcg[binary_name][arch][compiler] = {}
        if opt not in binary_to_fcg[binary_name][arch][compiler]:
            binary_to_fcg[binary_name][arch][compiler][opt] = []
        if binary_to_fcg[binary_name][arch][compiler][opt]:
            print(binary_to_fcg[binary_name][arch][compiler][opt])
            print(binary_fcg_path)
        binary_to_fcg[binary_name][arch][compiler][opt].append(binary_fcg_path)
    return binary_to_fcg


def analyze_opt_difference(binary_to_fcg):
    opt_difference = {}
    node_neighbor_difference = {}
    pbar = tqdm.tqdm(total=len(list(binary_to_fcg.keys())))
    for binary_name in binary_to_fcg:
        for arch in binary_to_fcg[binary_name]:
            for compiler in binary_to_fcg[binary_name][arch]:
                compiler_family = compiler.split("-")[0]
                if compiler_family not in opt_difference:
                    opt_difference[compiler_family] = {}
                if compiler_family not in node_neighbor_difference:
                    node_neighbor_difference[compiler_family] = {}
                opt_nodes = {}
                opt_fcg = {}
                for opt in binary_to_fcg[binary_name][arch][compiler]:
                    binary_fcg_path = binary_to_fcg[binary_name][arch][compiler][opt][0]
                    binary_fcg = read_pickle(binary_fcg_path)
                    fcg_nodes = list(binary_fcg.nodes())
                    opt_nodes[opt] = fcg_nodes
                    opt_fcg[opt] = binary_fcg
                opt_list = ["O0", "O1", "O2", "O3"]
                for index1, opt1 in enumerate(opt_list):
                    for index2 in range(index1 + 1, len(opt_list)):
                        # analyze node difference
                        opt2 = opt_list[index2]
                        opt_inter = list(set(opt_nodes[opt1]).intersection(set(opt_nodes[opt2])))
                        opt_union = list(set(opt_nodes[opt1]).union(set(opt_nodes[opt2])))
                        opt_ratio = len(opt_inter) / len(opt_union)
                        if opt1 + "-" + opt2 not in opt_difference[compiler_family]:
                            opt_difference[compiler_family][opt1 + "-" + opt2] = []
                        opt_difference[compiler_family][opt1 + "-" + opt2].append(opt_ratio)

                        # analyze node neighbor difference
                        if opt1 + "-" + opt2 not in node_neighbor_difference[compiler_family]:
                            node_neighbor_difference[compiler_family][opt1 + "-" + opt2] = []
                        fcg1 = opt_fcg[opt1]
                        fcg2 = opt_fcg[opt2]
                        for node in opt_inter:
                            opt1_node_neighbors = list(fcg1[node]) + list(fcg1.predecessors(node))
                            opt2_node_neighbors = list(fcg2[node]) + list(fcg2.predecessors(node))
                            nn_inter = list(set(opt1_node_neighbors).intersection(set(opt2_node_neighbors)))
                            nn_union = list(set(opt1_node_neighbors).union(set(opt2_node_neighbors)))
                            if nn_union:
                                nn_ratio = len(nn_inter) / len(nn_union)
                                node_neighbor_difference[compiler_family][opt1 + "-" + opt2].append(nn_ratio)

        pbar.update()
    pbar.close()
    return opt_difference, node_neighbor_difference


def main():
    fcg_pkl_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    project_name_list = os.listdir(fcg_pkl_folder)
    binary_fcg_paths_list = []
    for project_name in project_name_list:
        binary_project_dir = os.path.join(fcg_pkl_folder, project_name)
        binary_fcg_paths = read_binary_list(binary_project_dir)
        binary_fcg_paths_list += binary_fcg_paths

    binary_to_fcg = classify_binaries_by_name(binary_fcg_paths_list)
    write_json("binary_to_fcg.json", binary_to_fcg)

    opt_difference, node_neighbor_difference = analyze_opt_difference(binary_to_fcg)
    write_json("opt_difference.json", opt_difference)
    write_json("node_neighbor_difference.json", node_neighbor_difference)


if __name__ == '__main__':
    # test()
    main()
