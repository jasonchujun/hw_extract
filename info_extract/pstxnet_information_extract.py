# Date  : 2021/7/1 9:57
# Author: ehzujnu
# File  : pstxnet_information_extract.py
from config import Config
from collections import defaultdict


class PSTXNetInfomationExtract:
    def get_all_nets(self):
        """
        获取各个节点之间的连接关系和属性信息
        :return:
        {
            'Z_LTU_ADC3_REFCLK_N3': {
                'net_path': '@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)Z_LTU_ADC3_REFCLK_N',
                'C_SIGNAL': '@visby_mob_top_lib.visby_mob_top(sch_1):page1_i4',
                'D2M9 2': {'pin_num': '2',
                         'pin_path': "@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)(CHIPS)",
                         'pin_name': "'CLKOUT0N'",
                         'CDS_PINID': 'CLKOUT0N'},
                'R27M9 1': {'pin_num': '1',
                          'pin_path': "@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)",
                          'pin_name': "'A'",
                          'CDS_PINID': 'A'}
            },
            'Z_LTU_ADC3_REFCLK_P3': {
                'net_path': '@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1):Z_LTU_ADC3_REFCLK_P',
                'C_SIGNAL': '@visby_mob_top_lib.visby_mob_top(sch_1)',
                'D2M9 1': {'pin_num': '1',
                         'pin_path': "@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)(CHIPS)",
                         'pin_name': "'CLKOUT0'",
                         'CDS_PINID': 'CLKOUT0'},
                'R26M9 1': {'pin_num': '1',
                          'pin_path': "@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)(CHIPS)",
                          'pin_name': "'A'",
                          'CDS_PINID': 'A'}
            }
        }
        """
        all_net_dict = defaultdict()
        pstchip_path = Config.base_path.format(folder_name=Config.folder_name, proj_name=Config.proj_name,
                                               file_name=Config.pstxnet_file_name)
        with open(pstchip_path, "r", encoding="utf8") as f:
            data = f.readlines()
        line_datas = [i.strip() for i in data]

        line_filter_datas = []
        i = 0
        while i < len(line_datas):
            if line_datas[i].endswith("~"):
                line_datas[i] = line_datas[i][:-1] + line_datas[i + 1]
                line_datas.pop(i + 1)
            else:
                line_filter_datas.append(line_datas[i])
                i += 1

        net_start_list = []
        for i in range(len(line_filter_datas)):
            if line_filter_datas[i] == "NET_NAME":
                net_start_list.append(i)
            if line_filter_datas[i] == "END.":
                net_start_list.append(i)

        net_tuple = [(net_start_list[i], net_start_list[i + 1]) for i in range(len(net_start_list) - 1)]
        for nt in net_tuple:
            net_dict = self.__each_net_information_extract(line_datas[nt[0]:nt[1]])
            all_net_dict.update(net_dict)

        return all_net_dict

    def __each_net_information_extract(self, net_information):
        """
        获取每个net的信息
        :param net_information: 每个net组成的列表
        :return: 每个net的字典
        """
        net_dict = defaultdict()
        net_dict[net_information[1][1:-1]] = defaultdict()
        net_dict[net_information[1][1:-1]]["net_path"] = net_information[2].replace("'", "")[:-1]
        res = net_information[3].split("=")
        net_dict[net_information[1][1:-1]][res[0]] = res[1][1:-2]

        node_start_list = []
        for i in range(len(net_information)):
            if net_information[i].startswith("NODE_NAME"):
                node_start_list.append(i)
        node_start_list.append(len(net_information))

        node_tuple = [(node_start_list[i], node_start_list[i + 1]) for i in range(len(node_start_list) - 1)]
        for nt in node_tuple:
            node_dict = self.__each_node_information_extract(net_information[nt[0]:nt[1]])
            net_dict[net_information[1][1:-1]].update(node_dict)

        return net_dict

    def __each_node_information_extract(self, node_information):
        """
        提取每个连接节点node的属性信息
        :param node_information: 各个节点的列表
        :return: 各个节点属性组成的字典
        """
        split_result = node_information[0].split(" ")
        split_result = [i for i in split_result if i]

        node_dict = defaultdict()
        # 以part_name+pin_num联合作为主键，避免主键重复
        ndk = split_result[1] + Config.joint_mark + split_result[2]
        node_dict[ndk] = defaultdict()
        node_dict[ndk]["pin_num"] = split_result[2]
        node_dict[ndk]["pin_path"] = node_information[1][1:-2]
        split_pin_name = node_information[2].split(":")

        pin_name_old = split_pin_name[0]
        pin_name_split = [i for i in pin_name_old.split("'") if i]
        if len(pin_name_split) > 1:
            pin_name = ' '.join(pin_name_split)
        else:
            pin_name = ''.join(pin_name_split)

        node_dict[ndk]["pin_name"] = pin_name
        if len(split_pin_name) >= 2:
            res = split_pin_name[1].split("=")
            node_dict[ndk]["CDS_PINID"] = res[1][1:-2]

        return node_dict
