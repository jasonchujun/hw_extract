# Date  : 2021/7/6 17:42
# Author: ehzujnu
# File  : neo4j_info_extract.py
from info_extract.pstchip_information_extract import PSTChipInfomationExtract
from info_extract.pstxnet_information_extract import PSTXNetInfomationExtract
from info_extract.pstxprt_information_extract import AllPartInfomationExtract
from info_extract.pxl_information_extract import PXLStateExtract
from neo4j import GraphDatabase
from utils.tools import combine_dict
from multiprocessing import Process, Queue
import time

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Zhujunpwd1989$"))
relationship_CQL_queue = Queue()


# relationship_CQL_list = Manager().list([])


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
        CQL_string_list = self.__add_pgnd_node(CQL_string_list)

        return CQL_string_list

    def __add_pgnd_node(self, CQL_string_list):
        """
        添加一个PGND接地的节点
        :param CQL_string_list:  其他节点的CQL语句
        :return:  CQL字符串
        """
        pgnd_CQL = "merge(a:part{name:'PGND'})-[h:have]->(b:port{name:'PGND'})"
        CQL_string_list.append(pgnd_CQL)

        return CQL_string_list


class NEO4JCreate(object):
    def __init__(self):
        self.pnc = PinNodeCreate()

    def __filter_net_data(self):
        """
        将节点之间连接关系整理后返回, 每个第一项为是否为PGND判断，第二项为连接的属性，后面为各个节点
        :return:
        [[(1, "PGND"), (net_path, C_SIGNAL), (D2M9,  Y), (R27M9, A)...],
        [(0, "NOT_PGND"), (net_path, C_SIGNAL), (D6M12,  X), (R01M911, CDD 1)...]]
        """
        net_obj = PSTXNetInfomationExtract()
        net_info_dict = net_obj.get_all_nets()
        net_list = []
        for k, v in net_info_dict.items():
            mid_list = []
            mid_list.append((v["net_path"], v["C_SIGNAL"]))
            if k == "PGND":
                mid_list.insert(0, (1, "PGND"))
                for sk1 in v.keys():
                    if sk1 != "net_path" and sk1 != "C_SIGNAL":
                        mid_list.append((sk1.split(" ")[0], v[sk1]["pin_name"]))
            else:
                mid_list.insert(0, (0, "NOT_PGND"))
                for sk in v.keys():
                    if sk != "net_path" and sk != "C_SIGNAL":
                        mid_list.append((sk.split(" ")[0], v[sk]["pin_name"]))
            net_list.append(mid_list)

        return net_list

    def __get_all_connect_couple(self):
        """
        获取每个连接关系中，两两配对的节点, 第一个值是节点1和pin角名称，第二个值是，节点二和pin角名称，第三个值是关系属性
        :return: [[(D6M12,  X), (R01M911, CDD 1), (net_path, C_SIGNAL)],...]
        """
        net_list = self.__filter_net_data()
        connect_couple = []
        for nl in net_list:
            if nl[0][0] == 0:
                for n in range(2, len(nl)):
                    for m in range(n + 1, len(nl)):
                        connect_couple.append([nl[n], nl[m], nl[1]])
            else:
                for n in range(2, len(nl)):
                    pgnd_node = ("PGND", "PGND")
                    connect_couple.append([nl[n], pgnd_node, nl[1]])

        return connect_couple

    def __connect_CQL_create(self, part_a, port_a, part_b, port_b, n_path, c_sign):
        """
        传入两个节点关系，然后返回两个节点的互联CQL语句
        :param part_a: 节点1名称
        :param port_a: 节点1对应的pin角名称
        :param part_b: 节点2名称
        :param port_b: 节点2对应的pin角名称
        :param n_path: 关系属性n_path信息
        :param c_sign: 关系属性c_sign信息
        :return: 两个节点互联的CQL语句
        """

        s1 = "MATCH (a1:part{name:'" + part_a + "'})-[h1:have]->(b1:port{name:'" + port_a + "'}), (a2:part{name:'" + part_b + "'})-[h2:have]->(b2:port{name:'" + port_b + "'}) merge (b1)-[c:connect{net_path:'" + \
             n_path + "'," + "C_SIGNAL:'" + c_sign + "'}]->(b2)"
        s2 = " MATCH (a1:part{name:'" + part_b + "'})-[h1:have]->(b1:port{name:'" + port_b + "'}), (a2:part{name:'" + part_a + "'})-[h2:have]->(b2:port{name:'" + port_a + "'}) merge (b1)-[c:connect{net_path:'" + \
             n_path + "'," + "C_SIGNAL:'" + c_sign + "'}]->(b2)"

        return [s1, s2]

    def __relationship_CQL_create(self):
        """
        将所有节点创造两两配对后，生成对应的互联的CQL语句
        :return: 所有关系的CQL语句
        """
        CQL_connect_string = []
        connect_couple = self.__get_all_connect_couple()
        for cc in connect_couple:
            part_a, port_a, part_b, port_b, n_path, c_sign = cc[0][0].replace("\\", ""), cc[0][1].replace("\\", ""), \
                                                             cc[1][0].replace("\\", ""), cc[1][1].replace("\\", ""), \
                                                             cc[2][0].replace("\\", ""), cc[2][1].replace("\\", "")
            connect_list = self.__connect_CQL_create(part_a, port_a, part_b, port_b, n_path, c_sign)
            CQL_connect_string.extend(connect_list)

        return CQL_connect_string

    def node_create(self):
        """
        执行节点新增
        """
        exe_CQL_list = self.pnc.new_pin_node_CQL_create()
        for i in exe_CQL_list:
            def add_part_and_port(tx):
                tx.run(i)

            with driver.session() as session:
                session.write_transaction(add_part_and_port)

    def relationship_create(self, deal_queue):
        """
        生成各个pin角的联系关系
        """
        while not deal_queue.empty():
            CQL_string = deal_queue.get()

            def add_relationship(tx):
                tx.run(CQL_string)

            with driver.session() as session:
                session.write_transaction(add_relationship)

    def put_relationship_CQL_into_queue(self):
        """
        将消息放到queue队列中去
        """
        exe_CQL_list = self.__relationship_CQL_create()
        for record in exe_CQL_list:
            relationship_CQL_queue.put(record)

    def moutiprocess_task(self):
        ps = []
        for _ in range(10):
            p = Process(target=self.relationship_create, args=(relationship_CQL_queue,))
            ps.append(p)

        # 启动进程
        for p1 in ps:
            p1.start()


if __name__ == '__main__':
    nc = NEO4JCreate()
    st1 = time.time()
    nc.node_create()
    et1 = time.time()
    print("node over, cost time %s==================================================" % (et1 - st1))
    st2 = time.time()
    nc.put_relationship_CQL_into_queue()
    nc.moutiprocess_task()
    et2 = time.time()
    print("relationship over, cost time %s==================================================" % (et2 - st2))
