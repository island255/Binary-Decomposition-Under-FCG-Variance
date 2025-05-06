# coding=gbk
import os
import json
import seaborn as sns

from matplotlib import pyplot as plt, ticker


# plt.rcParams['font.family'] = 'SimHei'


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def draw_distribution_bar(ModX_normal_statistics, figure_name):
    number_keys = list(ModX_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    sorted(number_keys)
    cluster_numbers = []
    for key in number_keys:
        cluster_numbers.append(len(ModX_normal_statistics[str(key)]))
    plt.bar(number_keys, cluster_numbers)
    plt.yscale('log')
    plt.savefig(figure_name)
    plt.show()


def add_statistics(normal_statistics, result_dict):
    for number in result_dict:
        if number not in normal_statistics:
            normal_statistics[number] = []
        normal_statistics[number] += result_dict[number]
    return normal_statistics


def combine_two_dict(ModX_normal_statistics, ModX_inlining_statistics):
    ModX_statistics = add_statistics(ModX_normal_statistics, ModX_inlining_statistics)
    return ModX_statistics


def draw_similarity_box(ModX_normal_statistics, figure_name):
    number_keys = list(ModX_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    number_keys = sorted(number_keys)
    cluster_similarity = []
    for key in number_keys:
        key_similarities = ModX_normal_statistics[str(key)]
        cluster_similarity.append(key_similarities)

    plt.boxplot(cluster_similarity, number_keys, showfliers=False)
    plt.xticks(range(1, len(number_keys) + 1), labels=number_keys)
    # plt.ylim((0, 1))
    plt.savefig(figure_name)
    plt.show()


def draw_distribution_line(BMVul_normal_statistics, figure_name):
    ax = plt.subplot(111)
    number_keys = list(BMVul_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    number_keys = sorted(number_keys)
    cluster_numbers = []
    for key in number_keys:
        cluster_numbers.append(len(BMVul_normal_statistics[str(key)]))
    plt.plot(number_keys, cluster_numbers)
    plt.yscale('log')
    # plt.xscale('log')
    ax.set_xlabel(community_size, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel(community_number, fontsize=16)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(figure_name)
    plt.show()


def draw_distribution_line_for_BNVul(BMVul_normal_statistics, figure_name):
    ax = plt.subplot(111)
    number_keys = list(BMVul_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    number_keys = sorted(number_keys)
    cluster_numbers = []
    for key in number_keys:
        cluster_numbers.append(len(BMVul_normal_statistics[str(key)]))
    plt.plot(number_keys, cluster_numbers)
    plt.yscale('log')
    plt.xscale('log')
    ax.set_xlabel(community_size, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel(community_number, fontsize=16)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(figure_name)
    plt.show()


def draw_similarity_line_for_ModX(BMVul_normal_statistics, figure_name):
    ax = plt.subplot(111)
    number_keys = list(BMVul_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    number_keys = sorted(number_keys)
    cluster_similarity = []
    for key in number_keys:
        key_similarities = BMVul_normal_statistics[str(key)]
        cluster_similarity.append(sum(key_similarities) / len(key_similarities))

    plt.plot(number_keys, cluster_similarity, '*-', lw=3, ms=10)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
    # plt.xscale('log')
    # plt.xticks(range(1, len(number_keys) + 1), labels=number_keys)
    plt.ylim((0, 1))
    # plt.xlim((0, 14))
    ax.set_xlabel(community_size, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel(community_similarity, fontsize=16)
    plt.subplots_adjust(bottom=0.15, left=0.2)
    plt.savefig(figure_name)
    plt.show()


def draw_similarity_line_for_BMVul(BMVul_normal_statistics, figure_name):
    ax = plt.subplot(111)
    number_keys = list(BMVul_normal_statistics.keys())
    number_keys = [int(k) for k in number_keys]
    number_keys = sorted(number_keys)
    cluster_similarity = []
    for key in number_keys:
        key_similarities = BMVul_normal_statistics[str(key)]
        cluster_similarity.append(sum(key_similarities) / len(key_similarities))

    plt.plot(number_keys, cluster_similarity, '*-', lw=3, ms=10)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
    plt.xscale('log')
    # plt.xticks(range(1, len(number_keys) + 1), labels=number_keys)
    plt.ylim((0, 1))
    # plt.xlim((0, 14))
    ax.set_xlabel(community_size, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel(community_similarity, fontsize=16)
    plt.subplots_adjust(bottom=0.15, left=0.2)
    plt.savefig(figure_name)
    plt.show()


def evaluate_BMVul():
    BMVul_statistics_file = "BMVul_opt2opt_statistics.json"
    BMVul_statistics = read_json(BMVul_statistics_file)

    # draw_distribution_line(BMVul_normal_statistics, figure_name="BMVul\\BMVul_Normal_number_distribution.png")
    # draw_distribution_line(BMVul_inlining_statistics, figure_name="BMVul\\BMVul_inlining_number_distribution.png")
    #
    # draw_similarity_line(BMVul_normal_statistics, figure_name="BMVul\\BMVul_Normal_similarity_distribution.png")
    # draw_similarity_line(BMVul_inlining_statistics, figure_name="BMVul\\BMVul_Inlining_similarity_distribution.png")
    draw_distribution_line_for_BNVul(BMVul_statistics, figure_name="BMVul\\BMVul_number_distribution.png")
    draw_similarity_line_for_BMVul(BMVul_statistics, figure_name="BMVul\\BMVul_similarity_distribution.png")


def evaluate_ModX():
    ModX_statistics_file = "ModX_opt2opt_statistics.json"
    ModX_statistics = read_json(ModX_statistics_file)
    # draw_similarity_box(ModX_statistics, figure_name="ModX\\ModX_similarity_box_png")
    # draw_distribution_line(ModX_normal_statistics, figure_name="ModX\\ModX_Normal_number_distribution.png")
    # draw_distribution_line(ModX_inlining_statistics, figure_name="ModX\\ModX_inlining_number_distribution.png")
    #
    # draw_similarity_line(ModX_normal_statistics, figure_name="ModX\\ModX_Normal_similarity_distribution.png")
    # draw_similarity_line(ModX_normal_statistics, figure_name="ModX\\ModX_Inlining_similarity_distribution.png")

    draw_distribution_line(ModX_statistics, figure_name="ModX\\ModX_number_distribution.png")
    draw_similarity_line_for_ModX(ModX_statistics, figure_name="ModX\\ModX_similarity_distribution.png")


def main():
    evaluate_ModX()
    evaluate_BMVul()


if __name__ == '__main__':
    community_size = "Community Size"
    community_number = "Number"
    community_similarity = "Similarity"
    main()
