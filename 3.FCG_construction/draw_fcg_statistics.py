#encoding=gbk
import os
import json

import matplotlib.pyplot as plt


plt.rcParams['font.family'] = 'SimHei'



def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)


def main():
    summary_for_fcg_file = "summary_for_fcg.json"
    summary_for_fcg = read_json(summary_for_fcg_file)
    for arch in summary_for_fcg:
        for compiler in summary_for_fcg[arch]:
            for opt in summary_for_fcg[arch][compiler]:
                for statistic in summary_for_fcg[arch][compiler][opt]:
                    summary_for_fcg[arch][compiler][opt][statistic] = \
                        sum(summary_for_fcg[arch][compiler][opt][statistic]) / \
                        len(summary_for_fcg[arch][compiler][opt][statistic])

    summary_for_fcg_avg_file = "summary_for_fcg_avg.json"
    write_json(summary_for_fcg_avg_file, summary_for_fcg)


def draw_distribution_bar_for_8_compilers(attribute="nodes"):
    summary_for_fcg_file = "summary_for_fcg.json"
    summary_for_fcg = read_json(summary_for_fcg_file)
    arch = "x86_64"
    summary_for_fcg_per_arch = summary_for_fcg[arch]

    clang_compiler_list = ["clang-4.0", "clang-5.0", "clang-6.0", "clang-7.0"]
    gcc_compiler_list = ["gcc-4.9.4", "gcc-5.5.0", "gcc-6.5.0", "gcc-7.3.0"]
    compiler_list = gcc_compiler_list + clang_compiler_list
    opt_list = ["O0", "O1", "O2", "O3"]

    box_data = []
    box_labels = []
    for compiler in compiler_list:
        for opt in opt_list:
            nodes_info = summary_for_fcg_per_arch[compiler][opt][attribute]
            label = compiler + "-" + opt
            box_data.append(nodes_info)
            box_labels.append(label)
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=box_labels, sym='o', vert=True, whis=1.5, showfliers=False)
    ax.set_xticks(range(33))
    ax.set_xticklabels(
        ['',
         'O0', 'O1\n     gcc-4.9.4', 'O2', 'O3',
         'O0', 'O1\n     gcc-5.5.0', 'O2', 'O3',
         'O0', 'O1\n     gcc-6.4.0', 'O2', 'O3',
         'O0', 'O1\n     gcc-7.3.0', 'O2', 'O3',
         'O0', 'O1\n     clang-4.0', 'O2', 'O3',
         'O0', 'O1\n     clang-5.0', 'O2', 'O3',
         'O0', 'O1\n     clang-6.0', 'O2', 'O3',
         'O0', 'O1\n     clang-7.0', 'O2', 'O3',
         ],
        ha='center', fontsize=10)
    plt.xlabel("编译设置", fontsize=16)
    if attribute == "nodes":
        plt.ylabel("节点数量", fontsize=16)
    else:
        plt.ylabel("边数量", fontsize=16)
    plt.xticks(size=14)
    plt.yticks(size=14)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("8_compilers_" + attribute + ".png")
    plt.show()


def draw_gcc_distribution_bar(attribute="edges"):
    summary_for_fcg_file = "summary_for_fcg.json"
    summary_for_fcg = read_json(summary_for_fcg_file)
    arch = "x86_64"
    summary_for_fcg_per_arch = summary_for_fcg[arch]

    clang_compiler_list = ["clang-4.0", "clang-5.0", "clang-6.0", "clang-7.0",
                           "clang-8.0", "clang-9.0", "clang-10.0", "clang-11.0",
                           "clang-12.0", "clang-13.0"]
    gcc_compiler_list = ["gcc-4.9.4", "gcc-5.5.0", "gcc-6.5.0", "gcc-7.3.0",
                         "gcc-8.2.0", "gcc-9.4.0", "gcc-10.3.0", "gcc-11.2.0"]
    compiler_list = gcc_compiler_list + clang_compiler_list
    opt_list = ["O0", "O1", "O2", "O3", "Os", "Ofast"]

    box_data = []
    box_labels = []
    for compiler in gcc_compiler_list:
        for opt in opt_list:
            nodes_info = summary_for_fcg_per_arch[compiler][opt][attribute]
            label = compiler + "-" + opt
            box_data.append(nodes_info)
            box_labels.append(label)
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=box_labels, sym='o', vert=True, whis=1.5, showfliers=False)
    ax.set_xticks(range(49))
    ax.set_xticklabels(
        ['',
         'O0', 'O1\n     gcc-4.9.4', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-5.5.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-6.4.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-7.3.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-8.2.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-9.4.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-10.3.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     gcc-11.2.0', 'O2', 'O3', 'Os', 'Of',
         ],
        ha='center', fontsize=10)
    plt.xlabel("编译设置", fontsize=16)
    if attribute == "nodes":
        plt.ylabel("节点数量", fontsize=16)
    else:
        plt.ylabel("边数量", fontsize=16)
    plt.savefig("gcc_" + attribute + ".png")
    plt.show()


def draw_clang_distribution_bar(attribute="nodes"):
    summary_for_fcg_file = "summary_for_fcg.json"
    summary_for_fcg = read_json(summary_for_fcg_file)
    arch = "x86_64"
    summary_for_fcg_per_arch = summary_for_fcg[arch]

    clang_compiler_list = ["clang-4.0", "clang-5.0", "clang-6.0", "clang-7.0",
                           "clang-8.0", "clang-9.0", "clang-10.0", "clang-11.0",
                           "clang-12.0", "clang-13.0"]
    gcc_compiler_list = ["gcc-4.9.4", "gcc-5.5.0", "gcc-6.5.0", "gcc-7.3.0",
                         "gcc-8.2.0", "gcc-9.4.0", "gcc-10.3.0", "gcc-11.2.0"]
    compiler_list = gcc_compiler_list + clang_compiler_list
    opt_list = ["O0", "O1", "O2", "O3", "Os", "Ofast"]

    box_data = []
    box_labels = []
    for compiler in clang_compiler_list:
        for opt in opt_list:
            nodes_info = summary_for_fcg_per_arch[compiler][opt][attribute]
            label = compiler + "-" + opt
            box_data.append(nodes_info)
            box_labels.append(label)
    fig = plt.figure(figsize=(16, 6), dpi=120)
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=box_labels, sym='o', vert=True, whis=1.5, showfliers=False)
    ax.set_xticks(range(61))
    ax.set_xticklabels(
        ['',
         'O0', 'O1\n     clang-4.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-5.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-6.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-7.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-8.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-9.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-10.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-11.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-12.0', 'O2', 'O3', 'Os', 'Of',
         'O0', 'O1\n     clang-13.0', 'O2', 'O3', 'Os', 'Of',
         ],
        ha='center', fontsize=10)
    plt.xlabel("编译设置", fontsize=16)
    if attribute == "nodes":
        plt.ylabel("节点数量", fontsize=16)
    else:
        plt.ylabel("边数量", fontsize=16)
    plt.savefig("clang_" + attribute + ".png")
    plt.show()


if __name__ == '__main__':
    draw_distribution_bar_for_8_compilers("nodes")
    draw_distribution_bar_for_8_compilers("edges")
    # main()
    # draw_gcc_distribution_bar("nodes")
    # draw_gcc_distribution_bar("edges")
    # draw_clang_distribution_bar("nodes")
    # draw_clang_distribution_bar("edges")
