# Date  : 2021/6/29 17:38
# Author: ehzujnu
# File  : pxl_information_extract.py
from config import Config
from collections import defaultdict


class PXLStateExtract:
    def get_pxlstate(self):
        """
        获取PXL文件中每个元件的信息
        :return: 以元件名为key的字典
        {
            'X4': {'PATH_NAME':'@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)',
                   'SEC': '1',
                   'REUSE_ID': '26107',
                   'PRIM_FILE':'./flatlib/model_sym/mechanical/chips/chips.prt',
                   'PART_NAME': 'DISTANCEPIECE/1P2-SCS901024/2-SCS901024/2',
                   'LONG_PART_NAME': 'DISTANCEPIECE/1P2-SCS901024/2-SCS901024/2',
                   'PARENT_PPT_PHYS_PART': 'DISTANCEPIECE/1P2-SCS901024/2',
                   'PARENT_PPT': 'DISTANCEPIECE/1P2',
                   'PARENT_PPT_PART': 'DISTANCEPIECE/1P2-SCS901024/2',
                   'PARENT_CHIPS_PHYS_PART': 'DISTANCEPIECE/1P2'},
            'X5': {'PATH_NAME': '@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(SCH_1)',
                   'SEC': '1',
                   'REUSE_ID': '26106',
                   'PRIM_FILE': './flatlib/model_sym/mechanical/chips/chips.prt',
                   'PART_NAME': 'DISTANCEPIECE/1P2-SCS901024/2-SCS901024/2',
                   'LONG_PART_NAME': 'DISTANCEPIECE/1P2-SCS901024/2-SCS901024/2',
                   'PARENT_PPT_PHYS_PART': 'DISTANCEPIECE/1P2-SCS901024/2',
                   'PARENT_PPT': 'DISTANCEPIECE/1P2',
                   'PARENT_PPT_PART': 'DISTANCEPIECE/1P2-SCS901024/2',
                   'PARENT_CHIPS_PHYS_PART': 'DISTANCEPIECE/1P2'}
        }
        """
        all_pxlstate_dict = defaultdict()
        pxl_path = Config.base_path.format(folder_name=Config.folder_name, proj_name=Config.proj_name,
                                           file_name=Config.pxl_file_name)
        with open(pxl_path, "r", encoding="utf8") as f:
            data = f.readlines()
        line_datas = [i.strip() for i in data]

        pxl_start, pxl_end = 0, 0
        for i in range(len(line_datas)):
            if line_datas[i] == "BEGIN_PRIM:":
                pxl_start = i
            elif line_datas[i] == "END_PRIM;":
                pxl_end = i
                pxl_dict = self.__extract_pxl_detail(line_datas, pxl_start, pxl_end)
                all_pxlstate_dict.update(pxl_dict)

        return all_pxlstate_dict

    def __extract_pxl_detail(self, line_datas, pxl_start, pxl_end):
        """
        获取PXL中每个PRIM的详细信息
        :param line_datas:  每行数据组成的列表
        :param pxl_start:  PRIM的开始索引
        :param pxl_end:  PRIM的结束索引
        :return:  每个PRIM信息组成的字典
        """
        pxl_detail_dict = defaultdict()
        pxl_data = [i for i in line_datas[pxl_start:pxl_end] if
                    i not in ["BEGIN_PRIM:", "", "BEGIN_LIB_INFO:", "END_LIB_INFO;", "END_PRIM;"]]
        pxl_filter_list = []
        for pd in pxl_data:
            res = pd.split("=")
            util_name, util_value = res[0].strip(), res[1].strip()[1:-2]
            if util_name != "LOCATION":
                pxl_filter_list.append((util_name, util_value))
            else:
                pxl_filter_list.insert(0, (util_name, util_value))

        if pxl_filter_list[0][0] == "LOCATION":
            pxl_detail_dict[pxl_filter_list[0][1]] = defaultdict()
            for pfd in pxl_filter_list[1:]:
                pxl_detail_dict[pxl_filter_list[0][1]][pfd[0]] = pfd[1]

        return pxl_detail_dict
