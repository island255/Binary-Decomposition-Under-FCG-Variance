import time

from tqdm import tqdm
import numpy as np
from multiprocessing import Pool
import os
from single_models import KNN, LR, LDA, QDA, SVM, NBC
from utils import split_dataset_by_projects, extract_datas_and_target, read_csv, write_pickle


def write_evaluate_results(result_folder, model_name, labels, x, all_times):
    if os.path.exists(result_folder) is False:
        os.mkdir(result_folder)
    model_folder = os.path.join(result_folder, model_name)
    if os.path.exists(model_folder) is False:
        os.mkdir(model_folder)
    result_file_name = "iter_time-" + str(x) + ".pkl"
    result_file_path = os.path.join(model_folder, result_file_name)
    # np.savetxt(result_file_path, confusion_matrix)
    write_pickle(result_file_path, [labels, all_times])


def train_and_test_model(para_list):
    start_time = time.time()
    model, x, result_folder, training_data, training_label, testing_data, testing_label = para_list
    model_with_specific_para = model()
    model_name = model_with_specific_para.get_name()
    dest_file_path = os.path.join(result_folder, model_name,
                                  "iter_time-" + str(x) + ".pkl")
    if os.path.exists(dest_file_path):
        return
    model_initial_time = time.time()
    model_with_specific_para.train(training_data, training_label)
    model_train_time = time.time()
    predicted_labels = model_with_specific_para.predict(testing_data)
    model_predict_time = time.time()
    all_times = [start_time, model_initial_time, model_train_time, model_predict_time]

    # confusion_matrix = multilabel_confusion_matrix(testing_label, predicted_labels)
    write_evaluate_results(result_folder, model_name, [testing_label, predicted_labels], x, all_times)


def evaluate_single_model(iter_times, call_site_feature_and_labels, model, result_folder):
    parameter_list = []
    for x in range(iter_times):
        train_csv_content, test_csv_content, train_projects, test_projects = \
            split_dataset_by_projects(call_site_feature_and_labels)

        training_data, training_label = extract_datas_and_target(train_csv_content, type="train", number=10000)
        testing_data, testing_label = extract_datas_and_target(test_csv_content, type="test", number=10000)

        para_list = [model, x, result_folder, training_data, training_label, testing_data, testing_label]
        parameter_list.append(para_list)

    process_num = 10
    p = Pool(int(process_num))
    with tqdm(total=len(parameter_list)) as pbar:
        for i, res in tqdm(enumerate(p.imap_unordered(train_and_test_model, parameter_list))):
            pbar.update()
    p.close()
    p.join()


def evaluate_models():
    call_site_csv_file = "node_features_csv.csv"
    call_site_feature_and_labels = read_csv(call_site_csv_file)
    result_folder = "single_results"
    iter_times = 10
    for model in [KNN, LR, LDA, QDA, SVM, NBC]:
        print("evaluating model {}".format(model))
        evaluate_single_model(iter_times, call_site_feature_and_labels, model, result_folder)


if __name__ == '__main__':
    evaluate_models()
