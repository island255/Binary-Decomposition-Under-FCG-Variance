import json
import os
import pickle

import networkx as nx
from matplotlib import pyplot as plt
from networkx.drawing.nx_agraph import to_agraph


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def plot_graph(fcg):
    pos = nx.spring_layout(fcg)
    nx.draw(fcg, pos, with_labels=True, node_size=200)
    plt.show()


def draw_fcg(G1, G1_file):
    G1.graph['edge'] = {'arrowsize': '0.5'}  # 箭头大小
    G1.graph['node'] = {'shape': 'box'}  # 节点形状
    G1.graph['graph'] = {'splines': 'spline', 'rankdir': 'LR'}  # 线型与布局方向
    A = to_agraph(G1)
    A.layout('dot')  # 布局方法
    A.draw(G1_file)


def main():
    fcg_file = r"D:\binkit2\code\3.FCG_construction\pkl_example\a2ps-4.14_clang-10.0_arm_32_O0_fixnt.i64.fcg.fcg_pkl"
    fcg_O0 = read_pickle(fcg_file)
    fcg_O0_file = "fcg_O0.png"
    draw_fcg(fcg_O0, fcg_O0_file)
    fcg_file2 = r"D:\binkit2\code\3.FCG_construction\pkl_example\a2ps-4.14_clang-10.0_arm_32_O3_fixnt.i64.fcg.fcg_pkl"
    fcg_O3 = read_pickle(fcg_file2)
    fcg_O3_file = "fcg_O3.png"
    draw_fcg(fcg_O3, fcg_O3_file)


if __name__ == '__main__':
    main()