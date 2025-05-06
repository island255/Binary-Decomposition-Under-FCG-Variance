import time
from ensemble_models import KNN, LR, RF, GB, adaboost
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

    # 确保所有项目在10次迭代中都能成为测试集
    num_projects = len(all_project_name)
    test_size = max(1, int(num_projects * (1 - train_percent)))  # 至少1个项目作为测试集
    num_iterations = 10

    # 计算每个项目应该出现在测试集中的次数
    projects_per_iteration = [[] for _ in range(num_iterations)]
    for i, project in enumerate(all_project_name):
        iteration_idx = i % num_iterations
        projects_per_iteration[iteration_idx].append(project)

    # 确保每个迭代的测试集大小大致相同
    test_projects = []
    remaining_projects = all_project_name.copy()

    # 分配项目到当前迭代
    iteration_idx = iteration % num_iterations
    test_projects = projects_per_iteration[iteration_idx]

    # 如果测试项目太少，从剩余项目中补充
    if len(test_projects) < test_size:
        remaining = [p for p in remaining_projects if p not in test_projects]
        needed = test_size - len(test_projects)
        if needed > 0 and remaining:
            additional = random.sample(remaining, min(needed, len(remaining)))
            test_projects.extend(additional)

    # 如果测试项目太多，随机保留指定数量
    if len(test_projects) > test_size:
        test_projects = random.sample(test_projects, test_size)

    train_projects = list(set(all_project_name).difference(set(test_projects)))

    # 构建训练集和测试集
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
    # 合并两个数组
    combined_array = array1 + array2
    # 随机打乱数组顺序
    random.shuffle(combined_array)
    return combined_array


def extract_datas_and_target(call_site_csv_content, type="train", number=10000):
    if type == "train":
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
    else:
        data = []
        for line in call_site_csv_content[1:]:
            data.append(list(map(int, line)))
        data = [row[:-1] for row in data]
        label =[row[-1] for row in data]
    return numpy.array(data), numpy.array(label)


def write_evaluate_results(result_folder, model_name, n_estimators, labels, x, all_times):
    if os.path.exists(result_folder) is False:
        os.mkdir(result_folder)
    model_folder = os.path.join(result_folder, model_name)
    if os.path.exists(model_folder) is False:
        os.mkdir(model_folder)
    result_file_name = "n_estimators-" + str(n_estimators) + "-" + str(x) + ".pkl"
    result_file_path = os.path.join(model_folder, result_file_name)
    # np.savetxt(result_file_path, confusion_matrix)
    write_pickle(result_file_path, [labels, all_times])


def train_and_test_model(para_list):
    try:
        start_time = time.time()
        model, n_estimators, x, result_folder, test_binary_functions, \
            training_data, training_label, testing_data, testing_label = para_list
        model_with_specific_para = model(n_estimators)
        model_name = model_with_specific_para.get_name()
        dest_file_path = os.path.join(result_folder, model_name,
                                      "n_estimators-" + str(n_estimators) + "-" + str(x) + ".pkl")
        if os.path.exists(dest_file_path):
            return
        model_initial_time = time.time()
        model_with_specific_para.train(training_data, training_label)
        model_train_time = time.time()
        predicted_labels = model_with_specific_para.predict(testing_data)
        model_predict_time = time.time()
        all_times = [start_time, model_initial_time, model_train_time, model_predict_time]

        # confusion_matrix = multilabel_confusion_matrix(testing_label, predicted_labels)
        write_evaluate_results(result_folder, model_name, n_estimators,
                               [test_binary_functions, testing_label, predicted_labels], x, all_times)
    except:
        print("error")


def evaluate_single_model(iter_times, n_estimators_list, call_site_feature_and_labels, model, result_folder):
    parameter_list = []
    for x in range(iter_times):
        train_csv_content, test_csv_content, train_projects, test_projects, test_binary_functions = \
            split_dataset_by_projects(call_site_feature_and_labels, iteration=x)

        training_data, training_label = extract_datas_and_target(train_csv_content, type="train", number=100000)
        testing_data, testing_label = extract_datas_and_target(test_csv_content, type="test", number=100000000)
        print(len(training_data), len(testing_data))
        for n_estimators in n_estimators_list:
            print(x)
            para_list = [model, n_estimators, x, result_folder, test_binary_functions,
                         training_data, training_label, testing_data, testing_label]
            # parameter_list.append(para_list)
            train_and_test_model(para_list)

    # process_num = 4
    # p = Pool(int(process_num))
    # with tqdm(total=len(parameter_list)) as pbar:
    #     for i, res in tqdm(enumerate(p.imap_unordered(train_and_test_model, parameter_list))):
    #         pbar.update()
    # p.close()
    # p.join()


def evaluate_models():
    call_site_csv_file = "node_features_with_function_name_csv_x86_64.csv"
    call_site_feature_and_labels = read_csv(call_site_csv_file)
    result_folder = "results"
    iter_times = 10
    n_estimators_list = [300]
    for model in [adaboost]:
        print("evaluating model {}".format(model))
        evaluate_single_model(iter_times, n_estimators_list, call_site_feature_and_labels, model, result_folder)


if __name__ == '__main__':
    evaluate_models()
