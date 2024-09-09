import json
import pickle
import re

import graphviz


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def merge_duplicate_node(G):
    nodes_list = list(G.nodes())

    str_pattern = re.compile(r".*(_[0-9])$")
    for node in nodes_list:
        if str_pattern.match(node):
            node_strip = node[:-2]
            if node_strip in nodes_list:
                node_i_successors = list(G.successors(node))
                node_j_predecessors = list(G.predecessors(node))
                for node_i in node_i_successors:
                    G.add_edge(node_strip, node_i)
                for node_j in node_j_predecessors:
                    G.add_edge(node_j, node_strip)
                G.remove_node(node)
    return G


def draw_communities(O0_fcg, inlining_communities_O0, filename):
    g = graphviz.Digraph('G', filename=filename, format='pdf')
    for index, com in enumerate(inlining_communities_O0):
        with g.subgraph(name='cluster_' + str(index)) as c:
            c.attr(style='filled', color='lightgrey')
            c.node_attr.update(style='filled', color='white')
            for node in com:
                c.node(node)
            c.attr(label="community #" + str(index))
    # for node in O0_fcg.nodes():
    #     g.node(node)
    for edge in O0_fcg.edges():
        g.edge(edge[0], edge[1])
    g.view()


def get_common_nodes(O0_fcg, O3_fcg):
    nodes_O0 = list(O0_fcg.nodes())
    nodes_O3 = list(O3_fcg.nodes())
    common_nodes = list(set(nodes_O0).intersection(set(nodes_O3)))
    return common_nodes


def traverse_from_common_nodes(O0_fcg, common_nodes):
    inlining_communities_O0 = []
    for c_node in common_nodes:
        c_community = [c_node]
        c_node_successors = list(O0_fcg.successors(c_node))
        while c_node_successors:
            s_node = c_node_successors.pop()
            if s_node not in common_nodes and s_node not in c_community:
                c_community.append(s_node)
                c_node_successors += list(O0_fcg.successors(s_node))
        inlining_communities_O0.append(c_community)
    return inlining_communities_O0


def identify_inlined_functions(O0_mapping):
    O0_inlined_functions = []
    for bf in O0_mapping:
        bf_mapped_sfs = O0_mapping[bf]
        if len(bf_mapped_sfs) > 1:
            for sf in bf_mapped_sfs:
                sf_name = sf[1]
                if sf_name != bf:
                    O0_inlined_functions.append(sf_name)
    return O0_inlined_functions


def remove_inlined_node(common_nodes, O0_mapping, O3_mapping):
    normal_common_nodes = []
    O0_inlined_functions = identify_inlined_functions(O0_mapping)
    O3_inlined_functions = identify_inlined_functions(O3_mapping)
    for node in common_nodes:
        if node in O0_inlined_functions or node in O3_inlined_functions:
            continue
        else:
            normal_common_nodes.append(node)
    return normal_common_nodes


def identify_inlining_communities(O0_fcg, O3_fcg, O0_mapping, O3_mapping):
    common_nodes = get_common_nodes(O0_fcg, O3_fcg)
    common_nodes = remove_inlined_node(common_nodes, O0_mapping, O3_mapping)
    inlining_communities_O0 = traverse_from_common_nodes(O0_fcg, common_nodes)
    inlining_communities_O3 = traverse_from_common_nodes(O3_fcg, common_nodes)
    return inlining_communities_O0, inlining_communities_O3, common_nodes


def summarize_mapping_statistics(cluster_to_cluster_mappings, cluster_mapping_statistics=None):
    if cluster_mapping_statistics is None:
        cluster_mapping_statistics = {}
    for cluster1 in cluster_to_cluster_mappings:
        cluster1_list = cluster1.split("+")
        cluster1_len = len(cluster1_list)
        if cluster1_len not in cluster_mapping_statistics:
            cluster_mapping_statistics[cluster1_len] = []
        max_similarity = 0
        for cluster2 in cluster_to_cluster_mappings[cluster1]:
            similarity = cluster_to_cluster_mappings[cluster1][cluster2]
            if similarity >= max_similarity:
                max_similarity = similarity
        cluster_mapping_statistics[cluster1_len].append(max_similarity)
    return cluster_mapping_statistics


def get_bf_mapped_sfs(O0_cluster, O0_mapping):
    O0_mapping_to_sf = {}
    O0_cluster_to_inlining_flag = {}
    for com in O0_cluster:
        O0_mapping_to_sf[tuple(com)] = []
        inlining_flag = False
        for bf in com:
            if bf not in O0_mapping or O0_mapping[bf] == []:
                print("{} not in mapping".format(bf))
            else:
                if len(O0_mapping[bf]) > 1:
                    inlining_flag = True
                for sf_dict in O0_mapping[bf]:
                    sf_name = sf_dict[0].replace("/data1/jiaang/binkit2/Dataset/src/", "") + "+" + sf_dict[1]
                    O0_mapping_to_sf[tuple(com)].append(sf_name)
        O0_cluster_to_inlining_flag[tuple(com)] = inlining_flag
    return O0_mapping_to_sf, O0_cluster_to_inlining_flag


def evaluate_generated_clusters(O0_cluster, O3_cluster, O0_mapping, O3_mapping):
    normal_cluster_to_cluster_mappings = {}
    inlining_cluster_to_cluster_mappings = {}
    O0_mapping_to_sf, O0_cluster_to_inlining_flag = get_bf_mapped_sfs(O0_cluster, O0_mapping)
    O3_mapping_to_sf, O3_cluster_to_inlining_flag = get_bf_mapped_sfs(O3_cluster, O3_mapping)
    for O3_com in O3_mapping_to_sf:
        O3_com_mapped_sfs = O3_mapping_to_sf[O3_com]
        if not O3_com_mapped_sfs:
            continue
        if not O3_cluster_to_inlining_flag[O3_com]:
            normal_cluster_to_cluster_mappings["+".join(list(O3_com))] = {}
        else:
            inlining_cluster_to_cluster_mappings["+".join(list(O3_com))] = {}
        for O0_com in O0_mapping_to_sf:
            O0_com_mapped_sfs = O0_mapping_to_sf[O0_com]
            if set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)):
                similarity = len(list(set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)))) * 2 / \
                             (len(list(set(O3_com_mapped_sfs))) + len(list(set(O0_com_mapped_sfs))))
                if not O3_cluster_to_inlining_flag[O3_com]:
                    normal_cluster_to_cluster_mappings["+".join(list(O3_com))]["+".join(list(O0_com))] = similarity
                else:
                    inlining_cluster_to_cluster_mappings["+".join(list(O3_com))]["+".join(list(O0_com))] = similarity
    return {"normal_cluster_to_cluster_mappings": normal_cluster_to_cluster_mappings,
            "inlining_cluster_to_cluster_mappings": inlining_cluster_to_cluster_mappings}


def draw_anchor_nodes(O0_fcg, common_nodes, filename):
    g = graphviz.Digraph('G', filename=filename, format='pdf')
    all_nodes = list(O0_fcg.nodes())
    for node in all_nodes:
        if node in common_nodes:
            g.node(node, color='red')
        else:
            g.node(node, color='black')
    for edge in O0_fcg.edges():
        g.edge(edge[0], edge[1])
    g.view()


def draw_example():
    # O0_cluster_file = r"D:\binkit2\code\6.evaluate_existing_work\BMVul\example\a2ps-4.14_clang-10.0_arm_32_O0_fixnt.i64.fcg.fcg_pkl\clusters.json"
    # O3_cluster_file = r"D:\binkit2\code\6.evaluate_existing_work\BMVul\example\a2ps-4.14_clang-10.0_arm_32_O3_fixnt.i64.fcg.fcg_pkl\clusters.json"
    O0_fcg_file = r"D:\binkit2\code\7.get_anchor_nodes\pkl_example\a2ps-4.14_clang-10.0_arm_32_O0_fixnt.i64.fcg.fcg_pkl"
    O3_fcg_file = r"D:\binkit2\code\7.get_anchor_nodes\pkl_example\a2ps-4.14_clang-10.0_arm_32_O3_fixnt.i64.fcg.fcg_pkl"
    O0_fcg = read_pickle(O0_fcg_file)
    O3_fcg = read_pickle(O3_fcg_file)
    O0_fcg = merge_duplicate_node(O0_fcg)
    O3_fcg = merge_duplicate_node(O3_fcg)

    O0_mapping_file = r"D:\binkit2\code\7.get_anchor_nodes\mapping_example\a2ps-4.14_clang-10.0_arm_32_O0_fixnt_function_mapping.json"
    O3_mapping_file = r"D:\binkit2\code\7.get_anchor_nodes\mapping_example\a2ps-4.14_clang-10.0_arm_32_O3_fixnt_function_mapping.json"
    O0_mapping = read_json(O0_mapping_file)
    O3_mapping = read_json(O3_mapping_file)

    inlining_communities_O0, inlining_communities_O3, common_nodes = \
        identify_inlining_communities(O0_fcg, O3_fcg, O0_mapping, O3_mapping)

    # cluster_to_cluster_mappings = evaluate_generated_clusters(inlining_communities_O0, inlining_communities_O3,
    #                                                           O0_mapping, O3_mapping)
    # write_json("cluster_to_cluster_mappings.json", cluster_to_cluster_mappings)
    #
    # normal_cluster_mapping_statistics = summarize_mapping_statistics(
    #     cluster_to_cluster_mappings["normal_cluster_to_cluster_mappings"])
    # inlining_cluster_to_cluster_mappings = summarize_mapping_statistics(
    #     cluster_to_cluster_mappings["inlining_cluster_to_cluster_mappings"])
    # cluster_mapping_statistics = {"normal": normal_cluster_mapping_statistics,
    #                               "inlining": inlining_cluster_to_cluster_mappings}
    # write_json("cluster_mapping_statistics.json", cluster_mapping_statistics)

    # draw_communities(O0_fcg, inlining_communities_O0, "O0")
    # draw_communities(O3_fcg, inlining_communities_O3, "O3")
    draw_anchor_nodes(O0_fcg, common_nodes, "O0_common_nodes")
    draw_anchor_nodes(O3_fcg, common_nodes, "O3_common_nodes")


if __name__ == '__main__':
    # example_test()
    # example_test2()
    draw_example()
