# Date  : 2021/6/29 17:39
# Author: ehzujnu
# File  : pstchip_information_extract.py
from config import Config
from collections import defaultdict


class PSTChipInfomationExtract:
    def get_all_chips(self):
        """
        获取所有的chip信息
        :return: 一个字典
        {
        'UMF104009/10-UMF104009/10,10DBA': {
            'pin':
            {'3':{'PINUSE': 'GROUND', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'pin_name': 'Z'},
             '2':{'PINUSE': 'UNSPEC', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'pin_name': 'X'},
             '1':{'PINUSE': 'UNSPEC', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'ALLOW_CONNECT': 'TRUE', 'pin_name': 'Y'
                 }
            },
            'body':
            {'PART_NAME': 'UMF104009/10', 'BODY_NAME': 'UMF104009/10', 'LIB_TYPE': 'MISC', 'PHYS_DES_PREFIX': 'U', 'CLASS': 'DISCRETE', 'JEDEC_TYPE': '501-BYZ10903-267', 'ALT_SYMBOLS': '(501-BYZ10903-267)', 'TYPE': 'TYPE', 'CDS_LW_PART_NUMBER': 'UMF104009/10', 'VALUE': '10dB', 'PART_NUMBER': 'UMF104009/10', 'PARENT_PART_TYPE': 'UMF104009/10', 'SCH_MODIFIED_PART': 'TRUE', 'PARENT_PPT': 'UMF104009/10', 'PARENT_PPT_PART': 'UMF104009/10-UMF104009/10,10DB'
            }
        },
        'UMF104009/2-UMF104009/2':{
            'pin':
            {'3':{'PINUSE': 'GROUND', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'pin_name': 'Z'},
             '2':{'PINUSE': 'UNSPEC', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'pin_name': 'X'},
             '1':{'PINUSE': 'UNSPEC', 'NO_LOAD_CHECK': 'Both', 'NO_IO_CHECK': 'Both', 'NO_ASSERT_CHECK': 'TRUE', 'NO_DIR_CHECK': 'TRUE', 'ALLOW_CONNECT': 'TRUE', 'pin_name': 'Y'
                 }
            },
            'body':
            {'PART_NAME': 'UMF104009/2', 'BODY_NAME': 'UMF104009/2', 'LIB_TYPE': 'MISC', 'PHYS_DES_PREFIX': 'U', 'CLASS': 'DISCRETE', 'JEDEC_TYPE': '501-BYZ10903-267', 'ALT_SYMBOLS': '(501-BYZ10903-267)', 'TYPE': 'TYPE', 'CDS_LW_PART_NUMBER': 'UMF104009/2', 'VALUE': '2 dB', 'PART_NUMBER': 'UMF104009/2', 'PARENT_PART_TYPE': 'UMF104009/2', 'SCH_MODIFIED_PART': 'TRUE', 'PARENT_PPT': 'UMF104009/2', 'PARENT_PPT_PART': 'UMF104009/2-UMF104009/2,2 DB'
                }
            }
        }
        """
        all_chips_dict = defaultdict()
        pstchip_path = Config.base_path.format(folder_name=Config.folder_name, proj_name=Config.proj_name,
                                               file_name=Config.pstchip_file_name)
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

        prim_start, prim_end = 0, 0
        for i in range(len(line_filter_datas)):
            if line_filter_datas[i].startswith("primitive"):
                prim_start = i
            if line_filter_datas[i] == "end_primitive;":
                prim_end = i + 1
                res_dict = self.__extract_each_prim(line_filter_datas, prim_start, prim_end)
                all_chips_dict.update(res_dict)

        return all_chips_dict

    def __extract_each_prim(self, line_filter_datas, prim_start, prim_end):
        """
        提取所有整个prim节点的信息
        :param line_filter_datas:  过滤后只剩下prim信息的列表
        :param prim_start: 开始索引
        :param prim_end: 结束索引
        :return: prim_dict信息组成的字典
        """
        prim_data = line_filter_datas[prim_start:prim_end]
        prim_name = prim_data[0].split(" ")[1][1:-2]

        prim_dict = defaultdict()
        prim_dict[prim_name] = defaultdict()

        pin_start, pin_end, body_start, body_end = 0, 0, 0, 0
        for i in range(len(prim_data)):
            if prim_data[i] == "pin":
                pin_start = i
            if prim_data[i] == "end_pin;":
                pin_end = i + 1
                pin_dict = self.__extract_pin_information(prim_data, pin_start, pin_end)
                prim_dict[prim_name].update(pin_dict)

            if prim_data[i] == "body":
                body_start = i
            if prim_data[i] == "end_body;":
                body_end = i + 1
                body_dict = self.__extract_body_information(prim_data, body_start, body_end)
                prim_dict[prim_name].update(body_dict)

        return prim_dict

    def __extract_pin_information(self, line_filter_datas, pin_start, pin_end):
        """
        提取所有整个pin节点的信息
        :param line_filter_datas: 过滤后每个prim中所有pin信息的列表
        :param pin_start: pin开始的索引
        :param pin_end: pin结束的索引
        :return: pin信息组成的字典
        """
        pin_dict = defaultdict()
        pin_dict["pin"] = defaultdict()
        pin_data = line_filter_datas[pin_start:pin_end]

        pin_start_list = []
        for i in range(len(pin_data)):
            if pin_data[i].endswith(":"):
                pin_start_list.append(i)
        pin_start_list.append(len(pin_data))

        pin_start_list = [(pin_start_list[n], pin_start_list[n + 1]) for n in range(len(pin_start_list) - 1)]
        for ps in pin_start_list:
            e_pin_data = pin_data[ps[0]:ps[1]]
            pin_name_old = e_pin_data[0][:-1]
            pin_name_split = [i for i in pin_name_old.split("'") if i]
            if len(pin_name_split) > 1:
                pin_name = ' '.join(pin_name_split)
            else:
                pin_name = ''.join(pin_name_split)

            pin_dict["pin"][pin_name] = defaultdict()
            for m in e_pin_data[1:-1]:
                res = m.split("=")
                unit_name, unit_value = res[0].strip(), res[1].strip()[1:-2]
                pin_dict["pin"][pin_name][unit_name] = unit_value

        pin_dict = self.__change_to_pin_num(pin_dict)

        return pin_dict

    def __change_to_pin_num(self, pin_dict):
        """
        将提取的pin信息用pin_num的形式表示
        :param pin_dict: 提取后的chip信息字典
        :return: 以pin_num表示的chip信息字典
        """
        return_dict = defaultdict()
        return_dict["pin"] = defaultdict()

        for k1, v1 in pin_dict.items():
            for k, v in v1.items():
                pin_num_list = []
                mid_list = []
                v["pin_name"] = k
                pn = v.pop("PIN_NUMBER")[1:-1]
                if "," in pn:
                    res2 = pn.split(",")
                    mid_list.extend(res2)
                else:
                    mid_list.append(pn)

                for ml in mid_list:
                    if ".." in ml:
                        res1 = ml.split("..")
                        a = int(res1[0])
                        b = int(res1[1])
                        if a > b:
                            pin_num_list.extend(range(b, a + 1))
                        else:
                            pin_num_list.extend(range(a, b + 1))
                    else:
                        pin_num_list.append(ml)

                for pin_num in pin_num_list:
                    if pin_num != 0 and pin_num != "0":
                        pin_num = str(pin_num)
                        return_dict["pin"][pin_num] = v

            return return_dict

    def __extract_body_information(self, line_filter_datas, body_start, body_end):
        """
        提取pin中body信息
        :param line_filter_datas:  每个pin信息中的body列表
        :param body_start:  body的开始索引
        :param body_end:  body的结束索引
        :return: body信息的字典
        """
        body_dict = defaultdict()
        body_dict["body"] = defaultdict()
        body_data = line_filter_datas[body_start:body_end]

        for i in body_data[1:-1]:
            res = i.split("=")
            unit_name, unit_value = res[0].strip(), res[1].strip()[1:-2]
            body_dict["body"][unit_name] = unit_value

        return body_dict
