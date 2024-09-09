import os
import time
from multiprocessing import Pool

import networkx as nx
import pickle
import json
import copy

from tqdm import tqdm


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f)


def calculate_DS(G, community1):
    index_list = []
    for node in community1:
        node_index = G.nodes[node]["node_attribute"]["address_index"]
        if type(node_index) == list:
            index_list += node_index
        else:
            index_list.append(node_index)
    index_avg = sum(index_list) / len(index_list)
    DS = 0
    for index in index_list:
        DS += abs(index - index_avg)
    return DS


def calculate_locality_bias(G, community1, community2, function_number):
    DS1 = calculate_DS(G, community1)
    DS2 = calculate_DS(G, community2)
    DS_new = calculate_DS(G, community1 + community2)
    if DS_new > function_number / 100:
        return 0
    try:
        locality_bias = 3 * (1 - (DS_new - DS1 - DS2) / (function_number / 100))
    except:
        print(function_number, DS_new, DS1, DS2)
    return locality_bias


def calculate_EQ(G, community1):
    EQ1 = 0
    for node in community1:
        pre_node_list = G.predecessors(node)
        flag = True
        for pre_node in pre_node_list:
            if pre_node in community1:
                flag = False
                break
        if flag:
            EQ1 += 1
    return EQ1


def calculate_entry_limit_bias(G, community1, community2):
    EQ1 = calculate_EQ(G, community1)
    EQ2 = calculate_EQ(G, community2)
    EQ_new = calculate_EQ(G, community1 + community2)
    delta_EQ = EQ_new - (EQ1 + EQ2) / 2
    delta_bias = 2 ** (0 - delta_EQ)
    return delta_bias


def get_sum(node_i_predecessors, node_to_weight):
    total = 0
    for node in node_i_predecessors:
        if node in node_to_weight:
            total += node_to_weight[node]
    return total


def calculate_delta_Q(G, com1, com2, node_to_weight):
    delta_Q = 0
    W = sum(list(node_to_weight.values()))
    for node_i in com1:
        for node_j in com2:
            K_out_i = 0
            K_in_j = 0
            K_in_i = 0
            K_out_j = 0
            if G.has_edge(node_i, node_j):
                node_i_successors = list(G.successors(node_i))
                node_j_predecessors = list(G.predecessors(node_j))
                K_out_i = get_sum(node_i_successors, node_to_weight)
                K_in_j = get_sum(node_j_predecessors, node_to_weight)

            if G.has_edge(node_j, node_i):
                node_i_predecessors = list(G.predecessors(node_i))
                node_j_successors = list(G.successors(node_j))
                K_in_i = get_sum(node_i_predecessors, node_to_weight)
                K_out_j = get_sum(node_j_successors, node_to_weight)
            delta_Q += (K_in_i * K_out_j + K_out_i * K_in_j) * 2 / (W * 2)

    ar_in = 0
    as_in = 0
    ar_out = 0
    as_out = 0
    for node_i in com1:
        for node_j in com1:
            if G.has_edge(node_i, node_j):
                node_i_successors = list(G.successors(node_i))
                node_j_predecessors = list(G.predecessors(node_j))
                K_out_i = get_sum(node_i_successors, node_to_weight)
                K_in_j = get_sum(node_j_predecessors, node_to_weight)
                node_i_predecessors = list(G.predecessors(node_i))
                node_j_successors = list(G.successors(node_j))
                K_in_i = get_sum(node_i_predecessors, node_to_weight)
                K_out_j = get_sum(node_j_successors, node_to_weight)
                ar_in += K_in_j * K_out_i
                ar_out += K_out_j + K_in_i

    for node_i in com2:
        for node_j in com2:
            if G.has_edge(node_i, node_j):
                node_i_successors = list(G.successors(node_i))
                node_j_predecessors = list(G.predecessors(node_j))
                K_out_i = get_sum(node_i_successors, node_to_weight)
                K_in_j = get_sum(node_j_predecessors, node_to_weight)
                node_i_predecessors = list(G.predecessors(node_i))
                node_j_successors = list(G.successors(node_j))
                K_in_i = get_sum(node_i_predecessors, node_to_weight)
                K_out_j = get_sum(node_j_successors, node_to_weight)
                as_in += K_in_j * K_out_i
                as_out += K_out_j + K_in_i
    delta_Q -= 2 * (ar_in * as_in + ar_out * as_out) / (2 * W)
    return delta_Q


def summarize_node_obtained_Q(G, initial_partition, node_to_weight, function_number):
    merged_node_to_delta_Q = {}
    for index1 in range(0, len(initial_partition)):
        for index2 in range(index1 + 1, len(initial_partition)):
            flag = False
            for node1 in initial_partition[index1]:
                for node2 in initial_partition[index2]:
                    if G.has_edge(node1, node2):
                        flag = True
            if flag:
                locality_bias = calculate_locality_bias(G, initial_partition[index1], initial_partition[index2],
                                                        function_number)
                if locality_bias == 0:
                    merged_node_to_delta_Q[(index1, index2)] = 0
                    continue
                delta_Q = calculate_delta_Q(G, initial_partition[index1], initial_partition[index2], node_to_weight)

                entry_limit_bias = calculate_entry_limit_bias(G, initial_partition[index1], initial_partition[index2])
                merged_node_to_delta_Q[(index1, index2)] = delta_Q * locality_bias * entry_limit_bias
    return merged_node_to_delta_Q


def modx_decomposition(G, function_number):
    node_to_weight = propagate_weights(G)
    initial_partition = []
    for node in list(G.nodes()):
        initial_partition.append([node])
    inter_time = 0
    while True:
        inter_time += 1
        # print("iteration number {}".format(inter_time))
        merged_node_to_delta_Q = summarize_node_obtained_Q(G, initial_partition, node_to_weight,
                                                           function_number)
        best_union = max(merged_node_to_delta_Q, key=lambda x: merged_node_to_delta_Q[x])
        best_delta_Q = merged_node_to_delta_Q[best_union]
        if best_delta_Q > 0:
            index1, index2 = best_union
            initial_partition = (initial_partition[:index1] + initial_partition[index1 + 1:index2] +
                                 initial_partition[index2 + 1:] + [
                                     initial_partition[index1] + initial_partition[index2]])
        else:
            break
    best_partition = initial_partition
    return best_partition


def merge_node(G, cycle):
    new_node = "+".join(cycle)
    function_volume = 0
    address_index = []
    for node in cycle:
        function_volume += G.nodes[node]["node_attribute"]["function_volume"]
        if type(G.nodes[node]["node_attribute"]["address_index"]) is list:
            address_index += G.nodes[node]["node_attribute"]["address_index"]
        else:
            address_index.append(G.nodes[node]["node_attribute"]["address_index"])
    G.add_node(new_node, node_attribute={"function_volume": function_volume, "address_index": address_index})
    for node in cycle:
        in_edges = list(G.in_edges(node))
        for edge in in_edges:
            in_node = edge[0]
            if in_node not in cycle:
                G.add_edge(in_node, new_node)
        out_edges = list(G.out_edges(node))
        for edge in out_edges:
            out_node = edge[1]
            if out_node not in cycle:
                G.add_edge(new_node, out_node)
        G.remove_node(node)
    return G


def propagate_weights(G):
    c = 1
    # node_to_weight = extract_node_to_weight(G)
    node_to_weight = {}

    while list(nx.simple_cycles(G)):
        cycles = nx.simple_cycles(G)
        for cycle in cycles:
            G = merge_node(G, cycle)
            break

    while G:
        G = copy.deepcopy(G)
        end_nodes = extract_end_nodes(G)
        for node in end_nodes:
            node_to_weight[node] = G.nodes[node]["node_attribute"]["function_volume"]
        for node in end_nodes:
            node_predecessors = list(G.predecessors(node))
            for pre_node in node_predecessors:
                G.nodes[pre_node]["node_attribute"]["function_volume"] += c * 1 / len(node_predecessors) * \
                                                                          G.nodes[node]["node_attribute"][
                                                                              "function_volume"]
        for node in end_nodes:
            G.remove_node(node)
    return node_to_weight


def extract_end_nodes(G):
    end_nodes = []
    for node in G:
        calling_number = len(list(G.successors(node)))
        if calling_number == 0:
            end_nodes.append(node)
    return end_nodes


def construct_FCG_adding_function_volume(FCG, function_to_volume):
    delete_nodes = []
    all_address = []
    for node in FCG:
        start_address = FCG.nodes[node]["node_attribute"]["start_address"]
        if start_address in function_to_volume:
            all_address.append(start_address)
    sorted_address = list(sorted(all_address))
    function_number = len(sorted_address)
    for node in FCG:
        # debug_info = FCG.nodes[node]
        start_address = FCG.nodes[node]["node_attribute"]["start_address"]
        if start_address in function_to_volume:
            function_volume = function_to_volume[start_address]
            FCG.nodes[node]["node_attribute"]["function_volume"] = function_volume
            address_index = sorted_address.index(start_address)
            FCG.nodes[node]["node_attribute"]["address_index"] = address_index
        else:
            delete_nodes.append(node)
    for node in delete_nodes:
        FCG.remove_node(node)

    return FCG, function_number


def extract_function_volume(acfg_disasm_content):
    function_volume = {}
    for IDB_name in acfg_disasm_content:
        for binary_address in acfg_disasm_content[IDB_name]:
            if binary_address == "arch":
                continue
            binary_address_16 = int(binary_address, 16)
            if binary_address_16 not in function_volume:
                function_volume[binary_address_16] = 0
            for bb in acfg_disasm_content[IDB_name][binary_address]["basic_blocks"]:
                bb_len = acfg_disasm_content[IDB_name][binary_address]["basic_blocks"][bb]["bb_len"]
                function_volume[binary_address_16] += bb_len
    return function_volume


def run_ModX_dispatcher(arg_list):
    process_num = 4
    p = Pool(int(process_num))
    with tqdm(total=len(arg_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(run_ModX, arg_list))):
            pbar.update()
    p.close()
    p.join()


def run_ModX(arg_list):
    fcg_file_path, acfg_file_path, dest_result_folder, project_name, binary_file_name = arg_list
    dest_result_project_folder = os.path.join(dest_result_folder, project_name)
    if not os.path.exists(dest_result_project_folder):
        try:
            os.makedirs(dest_result_project_folder)
        except:
            pass
    dest_result_file = os.path.join(dest_result_folder, project_name, binary_file_name + ".json")
    if os.path.exists(dest_result_file):
        return
    FCG = read_pickle(fcg_file_path)
    acfg_disasm_content = read_json(acfg_file_path)
    function_to_volume = extract_function_volume(acfg_disasm_content)
    FCG_with_function_volume, function_number = construct_FCG_adding_function_volume(FCG, function_to_volume)
    # if function_number <= 1:
    #     print("fcg {} has only {} functions".format(fcg_file_path, function_number))
    #     return
    best_partition = modx_decomposition(FCG_with_function_volume, function_number)
    write_json(dest_result_file, best_partition)


def main():
    FCG_folder = "/data1/jiaang/binkit2/3.FCG_construction/FCG_pkl"
    acfg_folder = "/data1/jiaang/binkit2/0.preprocessing/IDA_scripts/IDA_acfg_disasm/acfg_disasm_dataset_I"
    dest_result_folder = "/data1/jiaang/binkit2/5.implement_strategy_of_existing_works/ModX/results"
    project_name_list = os.listdir(FCG_folder)
    arg_list = []
    for project_name in project_name_list:
        project_dir = os.path.join(FCG_folder, project_name)
        for fcg_file_name in os.listdir(project_dir):
            if not fcg_file_name.endswith(".fcg_pkl"):
                continue
            fcg_file_path = os.path.join(project_dir, fcg_file_name)
            binary_file_name = fcg_file_name.replace(".i64.fcg.fcg_pkl", "")
            acfg_file_name = binary_file_name + "_acfg_disasm.json"
            acfg_file_path = os.path.join(acfg_folder, acfg_file_name)
            if "_mips_" in binary_file_name:
                continue
            arg_list.append(
                [fcg_file_path, acfg_file_path, dest_result_folder, project_name, binary_file_name])
    run_ModX_dispatcher(arg_list)


if __name__ == '__main__':
    main()
