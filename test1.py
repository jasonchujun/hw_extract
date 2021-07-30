# Date  : 2021/7/12 15:01
# Author: ehzujnu
# File  : test1.py
from info_extract.pstchip_information_extract import PSTChipInfomationExtract
from info_extract.pstxprt_information_extract import AllPartInfomationExtract
from info_extract.pxl_information_extract import PXLStateExtract
from neo4j import GraphDatabase
from utils.tools import combine_dict

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Zhujunpwd1989$"))


class PartNodeCreate(object):
    def __init__(self):
        """
        初始化生成两个类
        """
        self.apie = AllPartInfomationExtract()
        self.pxls = PXLStateExtract()

    def __part_node_info_combine(self):
        """
        将每个part的信息组合起来
        :return:
        {
            'C47A0M0M1':{
                'library_part_name': 'RJC545201-15P-15P,RJC5452012/15C',
                'REUSE_INSTANCE': 'RXFEM1',
                'REUSE_ID': '7925',
                'SUBDESIGN_SUFFIX': 'M1',
                'REUSE_NAME': 'RXFE',
                'REUSE_PID': '1730',
                'PATH_NAME': '@VISBY_MOB_TOP_LIB.VISBY_MOB_TOP(CHIPS)',
                'SEC': '1', 'PRIM_FILE': './flatlib/model_sym/capunpol/chips.prt',
                'PART_NAME': 'RJC545201-15P-15P,RJC5452012/15C',
                'LONG_PART_NAME': '',
                'PARENT_PPT_PHYS_PART': 'RJC545201-15P',
                'PARENT_PPT': 'RJC545201',
                'PARENT_PPT_PART': 'RJC545201-15P',
                'PARENT_CHIPS_PHYS_PART': 'RJC545201'
            }，
            'R15NM3':{
            ...
            }
        }
        """
        part_info = self.apie.get_all_parts()
        pxls_info = self.pxls.get_pxlstate()
        result_dict = combine_dict(part_info, pxls_info)

        return result_dict

    def new_part_node_CQL_create(self):
        """
        每一个新增的part都生成对应CQL语句
        :return: [(part_name, library_part_name, 对应的CQL语句), (...)]
        """
        part_node_list = []
        result_dict = self.__part_node_info_combine()
        for k, v in result_dict.items():
            part_node_CQL_string = "MERGE (a:part {"
            part_node_CQL_string = part_node_CQL_string + "name:'" + k + "'"

            for k1, v1 in v.items():
                part_node_CQL_string = part_node_CQL_string + "," + k1 + ":'" + v1 + "'"
            part_node_CQL_string = part_node_CQL_string + "})-[h:have]->(b:port {"
            part_node_list.append((k, v["library_part_name"], part_node_CQL_string))

        return part_node_list


class PinNodeCreate(object):
    def __init__(self):
        """
        初始化生成两个类
        """
        self.part_node = PartNodeCreate()
        self.pstcie = PSTChipInfomationExtract()

    def __point_exist_judge_CQL(self, tx, part_name):
        """
        执行查询part节点语句
        :param tx: 执行器
        :param part_name: 所需要查询的节点名字
        """
        tx.run("MATCH (a:part {name: $name}) return a", name=part_name)

    def __part_node_exist_judge(self, search_name):
        """
        判断是否已经存在该节点
        :param search_name: 所需要查询的节点名字
        :return: Bool类型数据
        """
        with driver.session() as session:
            search_result = session.read_transaction(self.__point_exist_judge_CQL, search_name)

        if search_result:
            return True
        else:
            return False

    def new_pin_node_CQL_create(self):
        """
        组成CQL执行语句
        :return:[CQL1, CQL2, CQL3, ...]
        """
        CQL_string_list = []
        part_node_result = self.part_node.new_part_node_CQL_create()
        chip_info = self.pstcie.get_all_chips()
        for part_name, library_part_name, part_node_string in part_node_result:
            pins = chip_info[library_part_name]["pin"]
            pin_count = 0
            for k_pin, v_pin in pins.items():
                pin_count += 1
                # 由于没有新增到neo4j中，所以一直是false
                judge_result = self.__part_node_exist_judge(part_name)
                if not judge_result and pin_count == 1:
                    pin_node_CQL = part_node_string + "name:'" + k_pin + "'"
                    for k4, v4 in v_pin.items():
                        pin_node_CQL = pin_node_CQL + "," + k4
                        pin_node_CQL = pin_node_CQL + ":'" + v4 + "'"
                    pin_node_CQL = pin_node_CQL + "})"
                    CQL_string_list.append(pin_node_CQL)

                else:
                    update_pin_node_CQL = "MATCH(a:part {name:'" + part_name + "'}) merge(a)-[h:have]->(b:port{"
                    update_pin_node_CQL = update_pin_node_CQL + "name:'" + k_pin + "'"
                    for k4, v4 in v_pin.items():
                        update_pin_node_CQL = update_pin_node_CQL + "," + k4
                        update_pin_node_CQL = update_pin_node_CQL + ":'" + v4 + "'"
                    update_pin_node_CQL = update_pin_node_CQL + "})"
                    CQL_string_list.append(update_pin_node_CQL)

        return CQL_string_list


def node_create():
    pnc = PinNodeCreate()
    CQL_string_list = pnc.new_pin_node_CQL_create()

    exe_CQL_list = CQL_string_list[:2]

    for i in exe_CQL_list:
        def add_part_and_port(tx):
            tx.run(i)

        with driver.session() as session:
            session.write_transaction(add_part_and_port)
