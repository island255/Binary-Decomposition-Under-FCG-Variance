import json
import os

import matplotlib.pyplot as plt
import numpy as np


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def read_features(anchor_features_dir):
    optimization_to_features = {}
    for anchor_file_name in os.listdir(anchor_features_dir):
        anchor_file_path = os.path.join(anchor_features_dir, anchor_file_name)
        anchor_feature = read_json(anchor_file_path)
        for optimization in anchor_feature:
            if optimization not in optimization_to_features:
                optimization_to_features[optimization] = {}
            for node_type in anchor_feature[optimization]:
                if node_type not in optimization_to_features[optimization]:
                    optimization_to_features[optimization][node_type] = {}
                for function_name in anchor_feature[optimization][node_type]:
                    for feature_type in anchor_feature[optimization][node_type][function_name]:
                        if feature_type not in optimization_to_features[optimization][node_type]:
                            optimization_to_features[optimization][node_type][feature_type] = []
                        optimization_to_features[optimization][node_type][feature_type].append(
                            anchor_feature[optimization][node_type][function_name][feature_type])

    return optimization_to_features


def draw_feature_distribution(optimization_to_features):
    optimizations = ["O0", "O1", "O2", "O3", "Os", "Ofast"]
    node_types = ["normal", "anchor"]
    feature_types = ["function_volume", "in_degree", "out_degree"]
    for feature_type in feature_types:
        feature_list = []
        label_list = []
        for optimization in optimizations:
            for node_type in node_types:
                feature_list.append(optimization_to_features[optimization][node_type][feature_type])
                label_list.append(optimization + "+" + node_type)

        figure, axes = plt.subplots(figsize=(14, 4))
        axes.boxplot(feature_list, labels=label_list, showfliers=False)
        plt.ylabel(feature_type)
        plt.savefig("feature_distribution\\" + feature_type + ".png")
        plt.show()


def main():
    anchor_features_dir = r"D:\binkit2\code\7.get_anchor_nodes\anchor_features"
    optimization_to_features = read_features(anchor_features_dir)
    write_json("optimization_to_features.json", optimization_to_features)
    draw_feature_distribution(optimization_to_features)


if __name__ == '__main__':
    main()
