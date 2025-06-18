# encoding=utf-8
import json
import os
import pickle
from multiprocessing import Pool
from itertools import combinations, product
from tqdm import tqdm


def read_json(file_path):
    """read json file from disk"""
    with open(file_path, "r") as f:
        load_dict = json.load(f)
        return load_dict


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)


def read_binary_list(projectdir):
    """get all binary file's path"""
    binary_paths = []
    for root, dirs, files in os.walk(projectdir):
        for file_name in files:
            if file_name.endswith(".fcg_pkl"):
                file_path = os.path.join(root, file_name)
                binary_paths.append(file_path)
    return binary_paths


def get_split_parts(elf_name):
    elf_name = elf_name.replace("_function_mapping.json", "")
    project, compiler, arch1, arch2, opt = elf_name.split("_")[:5]
    binary_name = "_".join(elf_name.split("_")[5:])
    return project, compiler, arch1 + "_" + arch2, opt, binary_name


def classify_mappings_by_name(binary_fcg_paths_list):
    binary_to_mapping = {}
    for binary_fcg_path in tqdm(binary_fcg_paths_list):
        elf_name = os.path.basename(binary_fcg_path)
        project, compiler, arch, opt, binary_name = get_split_parts(elf_name)
        if arch == "mips_32" or arch == "mips_64" or compiler == "clang-13.0":
            continue
        binary_name = project + "_" + binary_name
        if binary_name not in binary_to_mapping:
            binary_to_mapping[binary_name] = {}
        if arch not in binary_to_mapping[binary_name]:
            binary_to_mapping[binary_name][arch] = {}
        if compiler not in binary_to_mapping[binary_name][arch]:
            binary_to_mapping[binary_name][arch][compiler] = {}
        if opt not in binary_to_mapping[binary_name][arch][compiler]:
            binary_to_mapping[binary_name][arch][compiler][opt] = []
        if binary_to_mapping[binary_name][arch][compiler][opt]:
            print(binary_to_mapping[binary_name][arch][compiler][opt])
            print(binary_fcg_path)
        binary_to_mapping[binary_name][arch][compiler][opt].append(binary_fcg_path)
    return binary_to_mapping


def read_mapping_list(projectdir):
    binary_paths = []
    for root, dirs, files in os.walk(projectdir):
        for file_name in files:
            if file_name.endswith("_function_mapping.json"):
                file_path = os.path.join(root, file_name)
                binary_paths.append(file_path)
    return binary_paths


def process_binary_mappings_files(mapping_results_folder, binary_to_mappings_file):
    if not os.path.exists(binary_to_mappings_file):
        project_name_list = os.listdir(mapping_results_folder)
        binary_mapping_paths_list = []
        for project_name in project_name_list:
            binary_project_dir = os.path.join(mapping_results_folder, project_name)
            binary_mapping_paths = read_mapping_list(binary_project_dir)
            binary_mapping_paths_list += binary_mapping_paths
        binary_to_mappings = classify_mappings_by_name(binary_mapping_paths_list)
        write_json(binary_to_mappings_file, binary_to_mappings)
    else:
        binary_to_mappings = read_json(binary_to_mappings_file)
    return binary_to_mappings


def extract_b2s_mapping(mapping1):
    mapping1_bf2sf = {}
    mapping1_sf2bf = {}
    for bf in mapping1:
        sf_list = mapping1[bf]
        if sf_list:
            mapping1_bf2sf[bf] = []
            for sf_info in sf_list:
                sf = "&".join([sf_info[0], sf_info[1], str(sf_info[2][0])])
                mapping1_bf2sf[bf].append(sf)
                if sf not in mapping1_sf2bf:
                    mapping1_sf2bf[sf] = []
                mapping1_sf2bf[sf].append(bf)
    return mapping1_bf2sf, mapping1_sf2bf


def identify_osf(bf1, bf1_mapped_sf, fcg_file1):
    osf1 = ""
    flag = False
    for sf in bf1_mapped_sf:
        sf_name = sf.split("&")[1]
        if sf_name == bf1:
            flag = True
            osf1 = sf
    if flag:
        return osf1
    else:
        return osf1


def identify_b2b_mapping_type(common_sf, bf1, bf2, bf1_mapped_sf, bf2_mapped_sf, fcg_file1, fcg_file2):
    common_sf_function_name = common_sf.split("&")[1]
    osf1 = identify_osf(bf1, bf1_mapped_sf, fcg_file1)
    osf2 = identify_osf(bf2, bf2_mapped_sf, fcg_file2)
    if not osf1 or not osf2:
        return "mapping_error"
    if set(bf1_mapped_sf) == set(bf2_mapped_sf):
        if len(bf1_mapped_sf) == 1 and len(bf2_mapped_sf) == 1:
            assert bf1_mapped_sf == bf2_mapped_sf == [common_sf]
            return "identical"
        else:
            assert len(bf2_mapped_sf) > 1 and len(bf2_mapped_sf) > 1
            return "identical"
    elif osf1 == osf2 and common_sf == osf1 and common_sf == osf2:
        return "root-equivalent"
    else:
        return "relevant"


def classify_mappings_by_common_sf(mapping1_bf2sf, mapping1_sf2bf, mapping2_bf2sf, mapping2_sf2bf, fcg_file1,
                                   fcg_file2):
    mappings_by_type = {"identical": [], "root-equivalent": [], "relevant": []}
    sf1_list = list(mapping1_sf2bf.keys())
    sf2_list = list(mapping2_sf2bf.keys())
    traversed_bf_pairs = []
    common_sfs = list(set(sf1_list).intersection(sf2_list))
    diff_sfs = list(set(sf1_list).difference(set(sf2_list))) + list(set(sf2_list).difference(set(sf1_list)))
    for sf in common_sfs:
        bf_list1 = mapping1_sf2bf[sf]
        bf_list2 = mapping2_sf2bf[sf]
        for bf1 in bf_list1:
            bf1_mapped_sf = mapping1_bf2sf[bf1]
            for bf2 in bf_list2:
                if [bf1, bf2] in traversed_bf_pairs or [bf2, bf1] in traversed_bf_pairs:
                    continue
                bf2_mapped_sf = mapping2_bf2sf[bf2]
                b2b_type = identify_b2b_mapping_type(sf, bf1, bf2, bf1_mapped_sf, bf2_mapped_sf, fcg_file1, fcg_file2)
                traversed_bf_pairs += [[bf1, bf2]]
                if b2b_type == "mapping_error":
                    continue
                mappings_by_type[b2b_type].append([bf1, bf2])
    return mappings_by_type


def convert_mapping_path_to_fcg_path(FCG_folder, mapping_file1):
    elf_name = os.path.basename(mapping_file1).replace("_function_mapping.json", "")
    project_name = os.path.dirname(mapping_file1)
    fcg_file_name = elf_name + ".i64.fcg.fcg_pkl"
    fcg_file_path = os.path.join(FCG_folder, project_name, fcg_file_name)
    return fcg_file_path


def construct_b2b_mappings_for_b2s_mapping(mapping_file1, mapping_file2):
    FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl/"
    mapping1 = read_json(mapping_file1)
    mapping2 = read_json(mapping_file2)
    fcg_file1 = convert_mapping_path_to_fcg_path(FCG_folder, mapping_file1)
    fcg_file2 = convert_mapping_path_to_fcg_path(FCG_folder, mapping_file2)
    mapping1_bf2sf, mapping1_sf2bf = extract_b2s_mapping(mapping1)
    mapping2_bf2sf, mapping2_sf2bf = extract_b2s_mapping(mapping2)
    mappings_by_type = classify_mappings_by_common_sf(mapping1_bf2sf, mapping1_sf2bf, mapping2_bf2sf, mapping2_sf2bf,
                                                      fcg_file1, fcg_file2)
    return mappings_by_type


def process_opt_pair(cmd):
    """处理单个编译选项对的任务"""
    project_binary_name, comparison_type, group1, group2, mapping_file1, mapping_file2, b2b_type_results_folder = cmd
    arch1, compiler1, opt1 = group1
    arch2, compiler2, opt2 = group2

    # 根据比较类型生成不同的文件名
    if comparison_type == "cross_opt":
        result_file_name = f"{arch1}_{compiler1}_{opt1}_vs_{opt2}.json"
        project_binary_folder = os.path.join(b2b_type_results_folder, "result_cross_opt", project_binary_name)
    elif comparison_type == "cross_compiler":
        result_file_name = f"{arch1}_{compiler1}_vs_{compiler2}_{opt1}.json"
        project_binary_folder = os.path.join(b2b_type_results_folder, "result_cross_compiler", project_binary_name)
    elif comparison_type == "cross_arch":
        result_file_name = f"{arch1}_vs_{arch2}_{compiler1}_{opt1}.json"
        project_binary_folder = os.path.join(b2b_type_results_folder, "result_cross_arch", project_binary_name)

    result_file_path = os.path.join(project_binary_folder, result_file_name)

    if os.path.exists(result_file_path):
        return

    if not os.path.exists(project_binary_folder):
        try:
            os.makedirs(project_binary_folder)
        except:
            pass

    b2b_mappings_by_type = construct_b2b_mappings_for_b2s_mapping(mapping_file1, mapping_file2)
    write_json(result_file_path, b2b_mappings_by_type)


def analyze_mapping_statistics(project_binary_name, binary_name_to_mappings, b2b_type_results_folder):
    """分析映射统计信息，为每种比较类型创建任务"""

    cmd_list = []

    # 收集所有架构、编译器和选项的组合
    all_groups = []
    for arch in binary_name_to_mappings:
        for compiler in binary_name_to_mappings[arch]:
            for opt in binary_name_to_mappings[arch][compiler]:
                all_groups.append((arch, compiler, opt))

    # 1. 跨优化选项比较 (相同架构和编译器，不同选项)
    for group1 in all_groups:
        arch1, compiler1, opt1 = group1
        for group2 in all_groups:
            arch2, compiler2, opt2 = group2
            if arch1 == arch2 and compiler1 == compiler2 and opt1 != opt2:
                mapping_file1 = binary_name_to_mappings[arch1][compiler1][opt1][0]
                mapping_file2 = binary_name_to_mappings[arch2][compiler2][opt2][0]
                cmd = (project_binary_name, "cross_opt", group1, group2,
                       mapping_file1, mapping_file2, b2b_type_results_folder)
                cmd_list.append(cmd)

    # 2. 跨编译器比较 (相同架构和选项，不同编译器)
    for group1 in all_groups:
        arch1, compiler1, opt1 = group1
        for group2 in all_groups:
            arch2, compiler2, opt2 = group2
            if arch1 == arch2 and compiler1 != compiler2 and opt1 == opt2:
                mapping_file1 = binary_name_to_mappings[arch1][compiler1][opt1][0]
                mapping_file2 = binary_name_to_mappings[arch2][compiler2][opt2][0]
                cmd = (project_binary_name, "cross_compiler", group1, group2,
                       mapping_file1, mapping_file2, b2b_type_results_folder)
                cmd_list.append(cmd)

    # 3. 跨架构比较 (相同编译器和选项，不同架构)
    for group1 in all_groups:
        arch1, compiler1, opt1 = group1
        for group2 in all_groups:
            arch2, compiler2, opt2 = group2
            if arch1 != arch2 and compiler1 == compiler2 and opt1 == opt2:
                mapping_file1 = binary_name_to_mappings[arch1][compiler1][opt1][0]
                mapping_file2 = binary_name_to_mappings[arch2][compiler2][opt2][0]
                cmd = (project_binary_name, "cross_arch", group1, group2,
                       mapping_file1, mapping_file2, b2b_type_results_folder)
                cmd_list.append(cmd)

    return cmd_list


def analyze_mapping_statistics_dispatcher(binary_to_mappings, b2b_type_results_folder):
    """分发任务到多进程池"""
    # 首先收集所有需要处理的任务
    all_cmds = []
    for project_binary_name in binary_to_mappings:
        cmds = analyze_mapping_statistics(project_binary_name,
                                          binary_to_mappings[project_binary_name],
                                          b2b_type_results_folder)
        all_cmds.extend(cmds)

    # 使用多进程池处理所有任务
    process_num = 24
    with Pool(process_num) as p:
        with tqdm(total=len(all_cmds)) as pbar:
            for _ in p.imap_unordered(process_opt_pair, all_cmds):
                pbar.update()


def construct_b2b_mappings(mapping_results_folder, b2b_type_results_folder):
    binary_to_mappings_file = "binary_to_mappings.json"
    binary_to_mappings = process_binary_mappings_files(mapping_results_folder, binary_to_mappings_file)
    analyze_mapping_statistics_dispatcher(binary_to_mappings, b2b_type_results_folder)


def main():
    mapping_results_folder = "/data1/jiaang/binkit2/Dataset/mapping_results"
    b2b_type_results_folder = "/data1/jiaang/binkit2/4.construct_function_mapping/three_types_of_mappings/result_all_comparisons"
    construct_b2b_mappings(mapping_results_folder, b2b_type_results_folder)


# def test():
#     mapping_file1 = "a2ps-4.14_clang-10.0_arm_32_O0_a2ps_function_mapping.json"
#     mapping_file2 = "a2ps-4.14_clang-10.0_arm_32_O3_a2ps_function_mapping.json"
#     b2b_mapping = construct_b2b_mappings_for_b2s_mapping(mapping_file1, mapping_file2)
#     write_json("b2b_mapping.json", b2b_mapping)


if __name__ == '__main__':
    # test()
    main()