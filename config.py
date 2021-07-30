# Date  : 2021/6/29 10:45
# Author: ehzujnu
# File  : config.py
class Config:
    base_path = "../data/{folder_name}/worklib/{proj_name}/packaged/{file_name}"
    proj_name = "visby_mob_top"
    folder_name = "61_13031-roa1289924_1.20210330174239"

    pstxprt_file_name = "pstxprt.dat"
    pstchip_file_name = "pstchip.dat"
    pstxnet_file_name = "pstxnet.dat"
    pxl_file_name = "pxl.state"

    extract_base_path = "../extract_data/{file_name}"
    extract_combine_data = "combine_data.json"
    extract_chip_data = "chip_data.json"
    extract_net_data = "net_data.json"

    joint_mark = " "
    search_part_name = "R66M9" + joint_mark + "1"

    neo4j_username = "neo4j"
    neo4j_password = "Zhujunpwd1989$"

    process_number = 5
    data_cut_part = 3000

    connect_couple_part_num = 10
