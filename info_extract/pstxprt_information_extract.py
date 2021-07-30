# Date  : 2021/6/29 17:37
# Author: ehzujnu
# File  : pstxprt_information_extract.py
from config import Config
from collections import defaultdict


class AllPartInfomationExtract:
    def get_all_parts(self):
        """
        获取每个元器件的信息
        :return: 所有元器件信息组成的字典
        """
        all_part_dict = defaultdict()
        pstxprt_path = Config.base_path.format(folder_name=Config.folder_name, proj_name=Config.proj_name,
                                               file_name=Config.pstxprt_file_name)
        with open(pstxprt_path, "r", encoding="utf8") as f:
            data = f.readlines()
        line_datas = [i.strip() for i in data]

        part_list = []
        part_group = []
        for i in range(len(line_datas)):
            if line_datas[i] == "PART_NAME":
                part_group.append(i)
            if line_datas[i].startswith("SECTION_NUMBER") and part_group:
                part_start = part_group.pop()
                part_list.append((part_start, i - 1))

        for pn in part_list:
            part_dict = self.__extract_part_detail(line_datas, pn[0], pn[1])
            all_part_dict.update(part_dict)

        # part_start, part_end = 0, 0
        # for i in range(len(line_datas)):
        #     if line_datas[i] == "PART_NAME":
        #         part_start = i
        #     # elif line_datas[i] == "SECTION_NUMBER 1":
        #     if line_datas[i].startswith("SECTION_NUMBER"):
        #         part_end = i - 1
        #         part_dict = self.__extract_part_detail(line_datas, part_start, part_end)
        #         all_part_dict.update(part_dict)

        return all_part_dict

    def __extract_part_detail(self, line_datas, part_start, part_end):
        """
        获取每个元器件的每个部分信息
        :param line_datas:  每行信息组成的列表
        :param part_start:  每个部分的开始索引
        :param part_end:  每个部分的结束索引
        :return:  每个部分提取的信息所组成的字典
        """
        part_data = line_datas[part_start:part_end]

        part_dict = defaultdict()
        location_and_name = part_data[1].split(" ")

        part_dict[location_and_name[0]] = defaultdict()
        part_dict[location_and_name[0]]["library_part_name"] = location_and_name[1][1:-2]
        for i in part_data[2:]:
            result = [i.strip() for i in i.split("=")]
            part_dict[location_and_name[0]][result[0]] = result[1][1:-2]

        return part_dict
