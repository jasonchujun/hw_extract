# Date  : 2021/7/16 14:45
# Author: ehzujnu
# File  : py2neo_info_extract.py
from info_extract.pstchip_information_extract import PSTChipInfomationExtract
from info_extract.pstxnet_information_extract import PSTXNetInfomationExtract
from info_extract.pstxprt_information_extract import AllPartInfomationExtract
from info_extract.pxl_information_extract import PXLStateExtract
from py2neo import Graph, Node, Relationship, Subgraph
from py2neo.matching import NodeMatcher
from utils.tools import combine_dict
from multiprocessing import Queue
from config import Config
import time

graph = Graph("http://localhost:7474", auth=(Config.neo4j_username, Config.neo4j_password))
relationship_CQL_queue = Queue()


class PartNodeCreate(object):
    def __init__(self):
        """
        初始化生成两个类
        """
        self.apie = AllPartInfomationExtract()
        self.pxls = PXLStateExtract()
        self.pstcie = PSTChipInfomationExtract()

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

    def write_part_node_into_neo4j(self):
        """
        创建所有的part_node节点
        """
        chip_info = self.pstcie.get_all_chips()
        tx = graph.begin()
        nmatcher = NodeMatcher(graph=graph)
        result_dict = self.__part_node_info_combine()
        part_node_list = []
        for k, v in result_dict.items():
            exist_node = nmatcher.match("part", name=k).first()
            if not exist_node:
                lpn = v["library_part_name"]
                body_info = chip_info[lpn]["body"]
                part_node = Node("part", name=k)
                for k1, v1 in v.items():
                    part_node[k1] = v1

                for k2, v2 in body_info.items():
                    part_node[k2] = v2

                part_node_list.append(part_node)

        # 将接地的节点加入进去
        part_node_list.append(Node("part", name="PGND", library_part_name="PGND"))
        nodes = Subgraph(nodes=part_node_list)
        tx.create(nodes)
        tx.commit()


class PinNodeCreate(object):
    def __init__(self):
        """
        初始化生成两个类
        """
        self.pstcie = PSTChipInfomationExtract()

    def __get_all_part_nodes(self):
        """
        获取所有的已经新建的节点信息
        :return: 由节点组成的list
        """
        matcher = NodeMatcher(graph)
        part_nodes = matcher.match("part").all()

        return part_nodes

    def write_port_node_into_neo4j(self):
        """
        批量更新port节点信息
        """
        part_nodes = self.__get_all_part_nodes()
        chip_info = self.pstcie.get_all_chips()

        tx = graph.begin()
        part_port_relationship_list = []
        for pn in part_nodes:
            library_part_name = pn.get("library_part_name")
            if library_part_name != "PGND":
                if "pin" not in chip_info[library_part_name]:
                    print(library_part_name, chip_info[library_part_name])
                for pk, pv in chip_info[library_part_name]["pin"].items():
                    port_node = Node("port", name=pk)
                    for k, v in pv.items():
                        port_node[k] = v
                    prp = Relationship(pn, "HAVE", port_node)
                    part_port_relationship_list.append(prp)

            else:
                port_node = Node("port", name="PGND")
                prp = Relationship(pn, "HAVE", port_node)
                part_port_relationship_list.append(prp)

        rels = Subgraph(relationships=part_port_relationship_list)
        tx.create(rels)
        tx.commit()


class RelationshipCreate(object):

    def __filter_net_data(self):
        """
        将节点之间连接关系整理后返回, 每个第一项为是否为PGND判断，第二项为连接的属性，后面为各个节点
        :return:
        [[(1, "PGND"), (net_path, C_SIGNAL), (D2M9,  1), (R27M9, 2)...],
        [(0, "NOT_PGND"), (net_path, C_SIGNAL), (D6M12,  1), (R01M911, 3)...]]
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
                        mid_list.append((sk1.split(" ")[0], sk1.split(" ")[1]))
            else:
                mid_list.insert(0, (0, "NOT_PGND"))
                for sk in v.keys():
                    if sk != "net_path" and sk != "C_SIGNAL":
                        mid_list.append((sk.split(" ")[0], sk.split(" ")[1]))
            net_list.append(mid_list)

        return net_list

    def __get_all_connect_couple(self):
        """
        获取每个连接关系中，两两配对的节点, 第一个值是节点1和pin角名称，第二个值是，节点二和pin角名称，第三个值是关系属性
        :return: [[(D6M12,  1), (R01M911, 2), (net_path, C_SIGNAL)],...]
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

    def __cut_connect_couple_into_list(self, connect_couple):
        """
        将原先整体的连接关系对进行分切，分为几次更新写入NEO4J中
        :param connect_couple: 原始的连接关系对
        :return: 切割后的关系对列表
        """
        cut_list = []
        count_list = []
        count = 0
        each_part_count = len(connect_couple) // Config.connect_couple_part_num + 1

        for i in range(1, Config.connect_couple_part_num + 1):
            this_count = i * each_part_count
            count_list.append((count, this_count))
            count = this_count

        for cl in count_list:
            cut_list.append(connect_couple[cl[0]:cl[1]])

        return cut_list

    def nodes_connect_create(self):
        """
        将每个关系对通过批量的形式写入到NEO4J中
        """
        pina_string = "match(a:part)-[h:HAVE]->(b:port) return a,b"
        query_result = graph.run(pina_string)
        nodes_dict = dict()
        for i in query_result:
            list1 = [i[0]["name"], i[1]["name"]]
            key1 = " ".join(list1)
            nodes_dict[key1] = i[1]

        connect_couple = self.__get_all_connect_couple()
        cut_list = self.__cut_connect_couple_into_list(connect_couple)

        for cl in cut_list:
            tx = graph.begin()
            part_port_relationship_list = []

            try:
                for cc in cl:
                    n_path, c_sign = cc[2][0], cc[2][1]
                    part_a_key = " ".join(cc[0])
                    pina = nodes_dict[part_a_key]
                    part_b_key = " ".join(cc[1])
                    pinb = nodes_dict[part_b_key]

                    ra1 = Relationship(pina, "CONNECT", pinb)
                    ra1["net_path"], ra1["C_SIGNAL"] = n_path, c_sign

                    ra2 = Relationship(pinb, "CONNECT", pina)
                    ra2["net_path"], ra2["C_SIGNAL"] = n_path, c_sign

                    part_port_relationship_list.append(ra1)
                    part_port_relationship_list.append(ra2)

                rels = Subgraph(relationships=part_port_relationship_list)
                tx.create(rels)
                tx.commit()
            except Exception as e:
                print(e)
                tx.rollback()
                cl.append(cc)

    # def get_all_net_info(self, mid_queue):
    #     while not mid_queue.empty():
    #         graph = Graph("http://127.0.0.1:7474", auth=("neo4j", "Zhujunpwd1989$"))
    #         connect_couple = mid_queue.get()
    #         tx = graph.begin()
    #         part_port_relationship_list = []
    #         print("len of connect couple is ", len(connect_couple))
    #         st1 = time.time()
    #         try:
    #             for cc in connect_couple:
    #                 part_a, port_a, part_b, port_b, n_path, c_sign = cc[0][0], cc[0][1], cc[1][0], cc[1][1], cc[2][0], \
    #                                                                  cc[2][1]
    #                 pina_string = "match(a:part{name:'" + part_a + "'})-[h:HAVE]->(b:port{name:'" + port_a + "'}), (a1:part{name:'" + part_b + "'})-[h1:HAVE]->(b1:port{name:'" + port_b + "'}) return b,b1"
    #
    #                 pin_subgraph_nodes = graph.run(pina_string).to_subgraph().nodes
    #
    #                 # subgraph的nodes不支持索引获取！！！
    #                 pin_subgraph_nodes = list(pin_subgraph_nodes)
    #                 pina, pinb = pin_subgraph_nodes[0], pin_subgraph_nodes[1]
    #
    #                 ra1 = Relationship(pina, "CONNECT", pinb)
    #                 ra1["net_path"], ra1["C_SIGNAL"] = n_path, c_sign
    #
    #                 ra2 = Relationship(pinb, "CONNECT", pina)
    #                 ra2["net_path"], ra2["C_SIGNAL"] = n_path, c_sign
    #
    #                 part_port_relationship_list.append(ra1)
    #                 part_port_relationship_list.append(ra2)
    #
    #             rels = Subgraph(relationships=part_port_relationship_list)
    #             tx.create(rels)
    #             tx.commit()
    #         except Exception as ex:
    #             print(ex)
    #             mid_queue.put(connect_couple)
    #
    #         et1 = time.time()
    #         print("relationship create over, cost time is ", et1 - st1)
    #
    # def add_to_queue(self):
    #     connect_couple = self.__get_all_connect_couple()
    #
    #     count_list = []
    #     count = 0
    #     max_count = len(connect_couple) // Config.data_cut_part + 1
    #     for i in range(1, Config.data_cut_part + 1):
    #         this_count = i * max_count
    #         count_list.append((count, this_count))
    #         count = this_count
    #
    #     for n in count_list:
    #         relationship_CQL_queue.put(connect_couple[n[0]:n[1]])
    #
    # def moutiprocess_task(self):
    #     ps = []
    #     for _ in range(Config.process_number):
    #         p = Process(target=self.get_all_net_info, args=(relationship_CQL_queue,))
    #         ps.append(p)
    #
    #     # 启动进程
    #     for p1 in ps:
    #         p1.start()


def create_index():
    graph.run("CREATE CONSTRAINT ON (p:part) ASSERT p.part_name IS UNIQUE")
    graph.run("create index on:port(PIN_NUMBER)")


class AddCatalog(object):
    def add_catalog(self):
        pxl_data = PXLStateExtract().get_pxlstate()
        path_set = set()
        all_path_list=[]
        for k, v in pxl_data.items():
            if v["PATH_NAME"] not in path_set:
                path_set.add(v["PATH_NAME"])
                all_path_list.append(v["PATH_NAME"])
                print(v["PATH_NAME"])
        # print(path_set)
        # print(len(path_set))
        # print(len(all_path_list))


if __name__ == '__main__':
    st = time.time()
    panc = PartNodeCreate()
    panc.write_part_node_into_neo4j()

    pinc = PinNodeCreate()
    pinc.write_port_node_into_neo4j()
    et = time.time()
    print("cost time is ", et - st)

    create_index()

    rc = RelationshipCreate()
    rc.nodes_connect_create()
    et1 = time.time()
    print("add relationship cost time is ", et1 - et)

    # rc = RelationshipCreate()
    # rc.add_to_queue()
    # rc.moutiprocess_task()
    # ac = AddCatalog()
    # ac.add_catalog()
