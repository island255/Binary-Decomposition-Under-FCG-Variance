# encoding=utf-8
import json
import os
from multiprocessing import Pool
from tqdm import tqdm


def read_json(file_path):
    """读取JSON文件"""
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(file_path, obj):
    """写入JSON文件"""
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def extract_b2s_mapping(mapping):
    """提取二进制到源码的映射关系"""
    bf2sf = {}
    sf2bf = {}
    for bf in mapping:
        sf_list = mapping[bf]
        if sf_list:
            bf2sf[bf] = []
            for sf_info in sf_list:
                sf = "&".join([sf_info[0], sf_info[1], str(sf_info[2][0])])
                bf2sf[bf].append(sf)
                if sf not in sf2bf:
                    sf2bf[sf] = []
                sf2bf[sf].append(bf)
    return bf2sf, sf2bf


def identify_osf(bf, bf_mapped_sf):
    """识别原始源码函数(Original Source Function)"""
    for sf in bf_mapped_sf:
        sf_name = sf.split("&")[1]
        if sf_name == bf:
            return sf
    return ""


def identify_b2b_mapping_type(common_sf, bf1, bf2, bf1_mapped_sf, bf2_mapped_sf):
    """识别二进制到二进制的映射类型"""
    osf1 = identify_osf(bf1, bf1_mapped_sf)
    osf2 = identify_osf(bf2, bf2_mapped_sf)

    if not osf1 or not osf2:
        return "mapping_error"
    if set(bf1_mapped_sf) == set(bf2_mapped_sf):
        if len(bf1_mapped_sf) == 1 and len(bf2_mapped_sf) == 1:
            return "identical"
        else:
            return "identical"
    elif osf1 == osf2 and common_sf == osf1 and common_sf == osf2:
        return "root-equivalent"
    else:
        return "relevant"


def classify_mappings_by_common_sf(mapping1_bf2sf, mapping1_sf2bf, mapping2_bf2sf, mapping2_sf2bf):
    """根据共同的源码函数分类映射关系"""
    mappings_by_type = {"identical": [], "root-equivalent": [], "relevant": []}
    common_sfs = set(mapping1_sf2bf.keys()).intersection(set(mapping2_sf2bf.keys()))
    traversed_bf_pairs = []

    for sf in common_sfs:
        bf_list1 = mapping1_sf2bf[sf]
        bf_list2 = mapping2_sf2bf[sf]

        for bf1 in bf_list1:
            bf1_mapped_sf = mapping1_bf2sf[bf1]
            for bf2 in bf_list2:
                if [bf1, bf2] in traversed_bf_pairs or [bf2, bf1] in traversed_bf_pairs:
                    continue

                bf2_mapped_sf = mapping2_bf2sf[bf2]
                b2b_type = identify_b2b_mapping_type(sf, bf1, bf2, bf1_mapped_sf, bf2_mapped_sf)
                traversed_bf_pairs.append([bf1, bf2])

                if b2b_type != "mapping_error":
                    mappings_by_type[b2b_type].append([bf1, bf2])

    return mappings_by_type


def process_cross_compiler_opt_pair(cmd):
    """处理跨编译器跨优化选项的任务"""
    project_binary_name, group1, group2, mapping_file1, mapping_file2, output_folder = cmd
    arch1, compiler1, opt1 = group1
    arch2, compiler2, opt2 = group2

    # 创建结果文件夹
    result_folder = os.path.join(output_folder, project_binary_name)
    os.makedirs(result_folder, exist_ok=True)

    # 生成结果文件名
    result_file_name = f"{arch1}_{compiler1}_{opt1}_vs_{compiler2}_{opt2}.json"
    result_file_path = os.path.join(result_folder, result_file_name)

    # 如果结果文件已存在，跳过处理
    if os.path.exists(result_file_path):
        return

    # 读取映射文件
    mapping1 = read_json(mapping_file1)
    mapping2 = read_json(mapping_file2)

    # 提取映射关系
    mapping1_bf2sf, mapping1_sf2bf = extract_b2s_mapping(mapping1)
    mapping2_bf2sf, mapping2_sf2bf = extract_b2s_mapping(mapping2)

    # 分类映射关系
    mappings_by_type = classify_mappings_by_common_sf(
        mapping1_bf2sf, mapping1_sf2bf,
        mapping2_bf2sf, mapping2_sf2bf
    )

    # 保存结果
    write_json(result_file_path, mappings_by_type)


def analyze_cross_compiler_opt(binary_to_mappings, output_folder):
    """分析跨编译器跨优化选项的映射关系"""
    cmd_list = []

    for project_binary_name in binary_to_mappings:
        binary_mappings = binary_to_mappings[project_binary_name]
        all_groups = []

        # 收集所有架构、编译器和选项的组合
        for arch in binary_mappings:
            if "mips" in arch:
                continue
            for compiler in binary_mappings[arch]:
                if compiler == "clang-13.0":
                    continue
                for opt in binary_mappings[arch][compiler]:
                    all_groups.append((arch, compiler, opt))

        # 生成跨编译器跨优化选项的比较任务
        for group1 in all_groups:
            arch1, compiler1, opt1 = group1
            for group2 in all_groups:
                arch2, compiler2, opt2 = group2
                # 相同架构、不同编译器、不同优化选项
                if arch1 == arch2 and compiler1 != compiler2 and opt1 != opt2:
                    mapping_file1 = binary_mappings[arch1][compiler1][opt1][0]
                    mapping_file2 = binary_mappings[arch2][compiler2][opt2][0]
                    cmd = (
                        project_binary_name, group1, group2,
                        mapping_file1, mapping_file2, output_folder
                    )
                    cmd_list.append(cmd)

    # 使用多进程处理任务
    with Pool(processes=24) as pool:
        with tqdm(total=len(cmd_list)) as pbar:
            for _ in pool.imap_unordered(process_cross_compiler_opt_pair, cmd_list):
                pbar.update()


def main():
    # 输入文件夹和输出文件夹
    mapping_results_folder = "/data1/jiaang/binkit2/Dataset/mapping_results"
    output_folder = "/data1/jiaang/binkit2/4.construct_function_mapping/cross_compiler_and_opt/result"
    binary_to_mappings_file = "binary_to_mappings.json"
    # 处理映射文件并分析跨编译器跨优化选项的映射关系
    binary_to_mappings = read_json(binary_to_mappings_file) # 这里需要填充实际的映射数据
    analyze_cross_compiler_opt(binary_to_mappings, output_folder)


if __name__ == '__main__':
    main()