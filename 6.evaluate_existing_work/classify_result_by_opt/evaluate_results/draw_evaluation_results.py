# coding=gbk
import os
import json
import seaborn as sns

from matplotlib import pyplot as plt, ticker

plt.rcParams['font.family'] = 'SimHei'


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def calculate_avg_similarity(opt_statistics):
    sim_list = []
    for number in opt_statistics:
        sim_list += opt_statistics[number]
    return sum(sim_list) / len(sim_list)


def draw_similarity_opt_for_ModX(ModX_statistics, figure_name):
    opt_list = ["O0", "O1", "O2", "O3"]
    x_list = []
    x = 0
    value_list = []
    for index1 in range(len(opt_list)):
        for index2 in range(index1 + 1, len(opt_list)):
            opt1 = opt_list[index1]
            opt2 = opt_list[index2]
            opt_statistics = ModX_statistics[opt1][opt2]
            avg_sim = calculate_avg_similarity(opt_statistics)
            value_list.append(avg_sim)
            x_list.append(x)
            x += 1

    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(x_list, value_list, '*-', lw=3, ms=10)
    ax.set_xticklabels(
        ["",
         "O0-O1", "O0-O2", "O0-O3", "O1-O2", "O1-O3", "O2-O3"], fontsize=16
    )
    plt.yticks(size=16)
    plt.ylabel("社团相似度", fontsize=16)
    plt.xlabel("编译设置", fontsize=16)
    plt.subplots_adjust(bottom=0.15, left=0.15)
    plt.savefig("ModX_difference_opt.png")
    plt.show()


def evaluate_ModX():
    ModX_statistics_file = "ModX_opt2opt_statistics.json"
    ModX_statistics = read_json(ModX_statistics_file)

    # draw_distribution_line(ModX_statistics, figure_name="ModX\\ModX_number_distribution.png")
    # draw_similarity_line_for_ModX(ModX_statistics, figure_name="ModX\\ModX_similarity_distribution.png")

    draw_similarity_opt_for_ModX(ModX_statistics, figure_name="ModX\\ModX_opt_similarity_distribution.png")


def main():
    evaluate_ModX()
    # evaluate_BMVul()


if __name__ == '__main__':
    main()
