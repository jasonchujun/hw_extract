# Date  : 2021/6/29 10:46
# Author: ehzujnu
# File  : hw_infomation_extract.py
from info_extract.pxl_information_extract import PXLStateExtract
from info_extract.pstxprt_information_extract import AllPartInfomationExtract
from info_extract.pstxnet_information_extract import PSTXNetInfomationExtract
from info_extract.pstchip_information_extract import PSTChipInfomationExtract
from utils.tools import combine_dict
from config import Config
import json


def information_combine():
    """
    将part部分与PXL部分的信息想结合后组成一个字典
    :return:  信息结合后的字典
    """
    APT = AllPartInfomationExtract()
    part_info = APT.get_all_parts()

    pxls = PXLStateExtract()
    pxls_info = pxls.get_pxlstate()

    result_dict = combine_dict(part_info, pxls_info)

    combine_data_save_path = Config.extract_base_path.format(file_name=Config.extract_combine_data)
    json.dump(result_dict, open(combine_data_save_path, "w"))

    return result_dict


def save_chip_info():
    """
    将所有的chip信息保存为json文件
    """
    pstci = PSTChipInfomationExtract()
    res = pstci.get_all_chips()
    chip_data_save_path = Config.extract_base_path.format(file_name=Config.extract_chip_data)
    json.dump(res, open(chip_data_save_path, "w"))


def save_net_info():
    """
    将所有的节点连接信息保存为json文件
    """
    pstni = PSTXNetInfomationExtract()
    res = pstni.get_all_nets()
    net_data_save_path = Config.extract_base_path.format(file_name=Config.extract_net_data)
    json.dump(res, open(net_data_save_path, "w"))


def get_one_information(result_dict, search_part_name):
    """
    查询某个组件的信息和连接情况
    :param result_dict:  所有信息组成的字典
    :param search_part_name:  需要查询的组件
    """
    search_part_name_1 = search_part_name.split(Config.joint_mark)[0]
    attr = result_dict[search_part_name_1]
    print("attr is: ", attr)

    net_data = PSTXNetInfomationExtract().get_all_nets()
    conllect_list = []

    for k, v in net_data.items():
        if search_part_name in v.keys():
            mid_list = []
            if k == "PGND":
                mid_list.append([search_part_name, v[search_part_name]["CDS_PINID"], v[search_part_name]["pin_num"]])
                mid_list.append(["PGND"])
            else:
                for sk in v.keys():
                    if sk != "net_path" and sk != "C_SIGNAL":
                        mid_list.append([sk, v[sk]["CDS_PINID"], v[sk]["pin_num"]])
            conllect_list.append(mid_list)

    print(conllect_list)


if __name__ == '__main__':
    save_chip_info()
    save_net_info()
    result_dict = information_combine()
    get_one_information(result_dict, Config.search_part_name)
