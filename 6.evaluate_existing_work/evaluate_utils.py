import json
import pickle


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


def get_bf_mapped_sfs(O0_cluster, O0_mapping):
    O0_mapping_to_sf = {}
    O0_cluster_to_inlining_flag = {}
    for com in O0_cluster:
        O0_mapping_to_sf[tuple(com)] = []
        inlining_flag = False
        for bf in com:
            if bf not in O0_mapping or O0_mapping[bf] == []:
                continue
                # print("{} not in mapping".format(bf))
            else:
                if len(O0_mapping[bf]) > 1:
                    inlining_flag = True
                for sf_dict in O0_mapping[bf]:
                    sf_name = sf_dict[0].replace("/data1/jiaang/binkit2/Dataset/src/", "") + "+" + sf_dict[1]
                    O0_mapping_to_sf[tuple(com)].append(sf_name)
        O0_cluster_to_inlining_flag[tuple(com)] = inlining_flag
    return O0_mapping_to_sf, O0_cluster_to_inlining_flag


def evaluate_generated_clusters(O0_cluster, O3_cluster, O0_mapping, O3_mapping):
    cluster_to_cluster_mappings = {}
    O0_mapping_to_sf, O0_cluster_to_inlining_flag = get_bf_mapped_sfs(O0_cluster, O0_mapping)
    O3_mapping_to_sf, O3_cluster_to_inlining_flag = get_bf_mapped_sfs(O3_cluster, O3_mapping)
    for O3_com in O3_mapping_to_sf:
        O3_com_mapped_sfs = O3_mapping_to_sf[O3_com]
        if not O3_com_mapped_sfs:
            continue
        cluster_to_cluster_mappings["+".join(list(O3_com))] = {}
        for O0_com in O0_mapping_to_sf:
            O0_com_mapped_sfs = O0_mapping_to_sf[O0_com]
            if set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)):
                similarity = len(list(set(O3_com_mapped_sfs).intersection(set(O0_com_mapped_sfs)))) * 2 / \
                             (len(list(set(O3_com_mapped_sfs))) + len(list(set(O0_com_mapped_sfs))))
                cluster_to_cluster_mappings["+".join(list(O3_com))]["+".join(list(O0_com))] = similarity
    return cluster_to_cluster_mappings


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
