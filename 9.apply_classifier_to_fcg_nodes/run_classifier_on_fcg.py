import time

from tqdm import tqdm
import numpy as np
from multiprocessing import Pool
import os
from ensemble_models import KNN, LR, RF, GB, adaboost
from utils import split_dataset_by_projects, extract_datas_and_target, read_csv, write_pickle


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
        model, n_estimators, x, result_folder, test_binary_functions,\
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
