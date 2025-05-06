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
    ax.set_xlabel("Community Size", fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel("Number", fontsize=16)
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
    ax.set_xlabel("Community Size", fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel("Number", fontsize=16)
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
    plt.xlim((0, 14))
    ax.set_xlabel("Community Size", fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel("Similarity", fontsize=16)
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
    ax.set_xlabel("Community Size", fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.set_ylabel("Similarity", fontsize=16)
    plt.subplots_adjust(bottom=0.15, left=0.2)
    plt.savefig(figure_name)
    plt.show()


def evaluate_N2NMatcher():
    N2NMatcher_normal_statistics_file = "N2NMatcher_normal_statistics.json"
    N2NMatcher_inlining_statistics_file = "N2NMatcher_inlining_statistics.json"
    N2NMatcher_normal_statistics = read_json(N2NMatcher_normal_statistics_file)
    N2NMatcher_inlining_statistics = read_json(N2NMatcher_inlining_statistics_file)
    N2NMatcher_statistics = combine_two_dict(N2NMatcher_normal_statistics, N2NMatcher_inlining_statistics)

    draw_distribution_line_for_BNVul(N2NMatcher_statistics, figure_name="N2NMatcher_number_distribution.png")
    draw_similarity_line_for_BMVul(N2NMatcher_statistics, figure_name="N2NMatcher_similarity_distribution.png")


def main():
    # evaluate_ModX()
    # evaluate_BMVul()
    evaluate_N2NMatcher()


if __name__ == '__main__':
    main()
