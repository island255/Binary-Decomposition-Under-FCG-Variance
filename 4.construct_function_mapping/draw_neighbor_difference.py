#encoding=gbk
import os
import json

import matplotlib.pyplot as plt
from matplotlib import ticker

# plt.rcParams['font.family'] = 'SimHei'


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def draw_opt_difference():
    opt_difference_file = "node_neighbor_difference.json"
    opt_difference = read_json(opt_difference_file)
    box_labels = ["O0-O1", "O0-O2", "O0-O3", "O1-O2", "O1-O3", "O2-O3"]
    # box_labels = ["O0-O1", "O0-O2", "O0-O3", "O0-Os", "O0-Ofast", "O1-O2", "O1-O3", "O1-Os", "O1-Ofast",
    #               "O2-O3", "O2-Os", "O2-Ofast", "O3-Os", "O3-Ofast", "Os-Ofast"]
    box_data = []
    compiler_families = ["gcc", "clang"]
    for compiler in compiler_families:
        for bx in box_labels:
            box_data.append(opt_difference[compiler][bx])
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=box_labels*2, sym='o', vert=True, whis=1.5, showfliers=False)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
    ax.set_xticks(range(13))
    ax.set_xticklabels(
        ["",
         "O0-O1", "O0-O2", "O0-O3\n       -- gcc --", "O1-O2", "O1-O3", "O2-O3",
         "O0-O1", "O0-O2", "O0-O3\n      -- clang --", "O1-O2", "O1-O3", "O2-O3"], fontsize=16
    )
    plt.yticks(size=16)
    plt.ylabel("Node Similarity", fontsize=16)
    plt.xlabel("Compilation Settings", fontsize=16)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("node_neighbor_opt.png")
    plt.show()


def draw_opt_neighbor_difference_in_one_compiler(compiler):
    opt_difference_file = "node_neighbor_difference.json"
    opt_difference = read_json(opt_difference_file)
    # box_labels = ["O0-O1", "O0-O2", "O0-O3", "O1-O2", "O1-O3", "O2-O3"]
    box_labels = ["O0-O1", "O0-O2", "O0-O3", "O0-Os", "O0-Ofast", "O1-O2", "O1-O3", "O1-Os", "O1-Ofast",
                  "O2-O3", "O2-Os", "O2-Ofast", "O3-Os", "O3-Ofast", "Os-Ofast"]
    box_data = []
    compiler_families = ["gcc", "clang"]
    for bx in box_labels:
        box_data.append(opt_difference[compiler][bx])
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=box_labels, sym='o', vert=True, whis=1.5, showfliers=False)
    plt.xticks(fontsize=16, rotation=45)
    plt.yticks(fontsize=16)
    ax.set_xticks(range(16))
    ax.set_xticklabels(
        ["", "O0-O1", "O0-O2", "O0-O3", "O0-Os", "O0-Ofast", "O1-O2", "O1-O3", "O1-Os", "O1-Ofast",
         "O2-O3", "O2-Os", "O2-Ofast", "O3-Os", "O3-Ofast", "Os-Ofast"]
    )
    ax.set_xlabel("Compilation Settings", fontsize=16)
    ax.set_ylabel("Neighbor Similarity", fontsize=16)
    plt.subplots_adjust(bottom=0.25, left=0.15)
    plt.savefig(compiler + "_neighbor_difference.png")
    plt.show()


if __name__ == '__main__':
    draw_opt_neighbor_difference_in_one_compiler("clang")
    draw_opt_neighbor_difference_in_one_compiler("gcc")
