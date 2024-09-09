import json
import os


def read_json(file_path):
    with open(file_path, "r") as f:
        file_content = json.load(f)
        return file_content


def write_json(file_path, obj):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2)


def extract_opt_in_file_name(result_file):
    if "c++" in result_file:
        result_file = result_file.replace("c++", "")
    binary_name1 = result_file.split("+")[0]
    binary_name2 = result_file.split("+")[1].replace(".json", "")
    try:
        opt1 = binary_name1.split("_")[4]
        opt2 = binary_name2.split("_")[4]
        return opt1, opt2
    except:
        print(binary_name1, binary_name2)
        raise Exception


def get_avg(num_list):
    new_num_list = []
    for num in num_list:
        if num != 1:
            new_num_list.append(num)
    if new_num_list == []:
        return 0
    return sum(new_num_list) / len(new_num_list)


def main():
    anchor_community_folder = r"/data1/jiaang/binkit2/7.anchor_node_identification/summary_anchor_community"
    opt_list = ["O0", "O1", "O2", "O3"]
    opt_to_com_size = {}
    for binary_name in os.listdir(anchor_community_folder):
        binary_dir = os.path.join(anchor_community_folder, binary_name)
        for result_file in os.listdir(binary_dir):
            result_file_path = os.path.join(binary_dir, result_file)
            result = read_json(result_file_path)
            opt1, opt2 = extract_opt_in_file_name(result_file)
            if opt1 not in opt_list or opt2 not in opt_list or opt1 == opt2:
                continue
            opt1_num = int(opt1[1])
            opt2_num = int(opt2[1])
            if opt2_num > opt1_num:
                temp = opt1
                opt1 = opt2
                opt2 = temp
            if opt1 not in opt_to_com_size:
                opt_to_com_size[opt1] = {}
            if opt2 not in opt_to_com_size[opt1]:
                opt_to_com_size[opt1][opt2] = []
            if opt2_num > opt1_num:
                opt_to_com_size[opt1][opt2] = {opt1: get_avg(result["com2"]), opt2: get_avg(result["com1"])}
            else:
                opt_to_com_size[opt1][opt2] = {opt1: get_avg(result["com1"]), opt2: get_avg(result["com2"])}
    write_json("opt_to_com_size.json", opt_to_com_size)


if __name__ == '__main__':
    main()