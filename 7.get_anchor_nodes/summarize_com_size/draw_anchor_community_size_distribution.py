#encoding=gbk
import os
import json

import numpy as np
from matplotlib import pyplot as plt



plt.rcParams['font.family'] = 'SimHei'


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def draw_distribution(opt_to_com_size_file):
    opt_list = ["O0", "O1", "O2", "O3"]
    box_data = []
    for opt in opt_list:
        box_data.append(opt_to_com_size_file[opt])
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = fig.add_subplot(111)
    ax.boxplot(box_data, labels=opt_list, sym='o', vert=True, whis=1.5)
    plt.savefig("anchor_community_size.png")
    plt.show()


def draw_avg(opt_to_com_size):
    opt_list = ["O0", "O1", "O2", "O3"]
    avg_data_1 = []
    avg_data_2 = []
    label_list = []
    for index1 in range(0, 4):
        for index2 in range(index1 + 1, 4):
            label_list.append(opt_list[index1] + "-" + opt_list[index2])
            avg_data_1.append(opt_to_com_size[opt_list[index2]][opt_list[index1]][opt_list[index1]])
            avg_data_2.append(opt_to_com_size[opt_list[index2]][opt_list[index1]][opt_list[index2]])

    fig = plt.figure()
    x = np.arange(len(label_list))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width / 2, avg_data_1, width, label='低优化')
    rects2 = ax.bar(x + width / 2, avg_data_2, width, label='高优化')

    ax.set_xticks(x)
    ax.set_xticklabels(label_list)
    ax.legend()

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.xlabel("优化选项", fontsize=16)
    plt.ylabel("映射函数数量", fontsize=16)
    plt.subplots_adjust(bottom=0.15, left=0.15)
    plt.savefig("anchor_community_size.png")
    plt.show()


def main():
    opt_to_com_size_file = "opt_to_com_size.json"
    opt_to_com_size = read_json(opt_to_com_size_file)
    # draw_distribution(opt_to_com_size_file)
    draw_avg(opt_to_com_size)


if __name__ == '__main__':
    main()