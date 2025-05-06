import csv
import json
import os
import pickle
import random

import numpy



def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json_str = json.dumps(obj, indent=2)
        f.write(json_str)


def read_csv(call_site_csv_file):
    csv_reader = csv.reader(open(call_site_csv_file, "r"))
    csv_content = []
    for line in csv_reader:
        csv_content.append(line)
    return csv_content


def read_pickle(pickle_file):
    with open(pickle_file, "rb") as f:
        return pickle.load(f)


def write_pickle(pickle_file, obj):
    with open(pickle_file, "wb") as f:
        pickle.dump(obj, f)


def split_dataset_by_projects(call_site_feature_and_labels, train_percent=0.9, iteration=0):
    test_binary_functions = []
    all_project_name = []
    for line in call_site_feature_and_labels[1:]:
        if line[0] not in all_project_name:
            all_project_name.append(line[0])

    # ȷ��������Ŀ��10�ε����ж��ܳ�Ϊ���Լ�
    num_projects = len(all_project_name)
    test_size = max(1, int(num_projects * (1 - train_percent)))  # ����1����Ŀ��Ϊ���Լ�
    num_iterations = 10

    # ����ÿ����ĿӦ�ó����ڲ��Լ��еĴ���
    projects_per_iteration = [[] for _ in range(num_iterations)]
    for i, project in enumerate(all_project_name):
        iteration_idx = i % num_iterations
        projects_per_iteration[iteration_idx].append(project)

    # ȷ��ÿ�������Ĳ��Լ���С������ͬ
    test_projects = []
    remaining_projects = all_project_name.copy()

    # ������Ŀ����ǰ����
    iteration_idx = iteration % num_iterations
    test_projects = projects_per_iteration[iteration_idx]

    # ���������Ŀ̫�٣���ʣ����Ŀ�в���
    if len(test_projects) < test_size:
        remaining = [p for p in remaining_projects if p not in test_projects]
        needed = test_size - len(test_projects)
        if needed > 0 and remaining:
            additional = random.sample(remaining, min(needed, len(remaining)))
            test_projects.extend(additional)

    # ���������Ŀ̫�࣬�������ָ������
    if len(test_projects) > test_size:
        test_projects = random.sample(test_projects, test_size)

    train_projects = list(set(all_project_name).difference(set(test_projects)))

    # ����ѵ�����Ͳ��Լ�
    train_csv_content = [call_site_feature_and_labels[0][6:]]
    test_csv_content = [call_site_feature_and_labels[0][6:]]

    for line in call_site_feature_and_labels[1:]:
        if line[0] in train_projects:
            train_csv_content.append(line[6:])
        else:
            test_csv_content.append(line[6:])
            test_binary_functions.append([line[1], line[2], line[3]])

    return train_csv_content, test_csv_content, train_projects, test_projects, test_binary_functions


def mix_arrays(array1, array2):
    # �ϲ���������
    combined_array = array1 + array2
    # �����������˳��
    random.shuffle(combined_array)
    return combined_array


def extract_datas_and_target(call_site_csv_content, type="train", number=10000):
    data0 = []
    data1 = []
    for line in call_site_csv_content[1:]:
        label = int(line[-1])
        if label:
            data1.append(list(map(int, line)))
        else:
            data0.append(list(map(int, line)))
    if len(data0) > number:
        data0 = random.sample(data0, number)
    if len(data1) > number:
        data1 = random.sample(data1, number)

    final_data = mix_arrays(data0, data1)
    data = [row[:-1] for row in final_data]
    label = [row[-1] for row in final_data]
    return numpy.array(data), numpy.array(label)
