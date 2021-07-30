# Date  : 2021/7/6 17:43
# Author: ehzujnu
# File  : tools.py
from collections import defaultdict


def combine_dict(dict_a, dict_b):
    res_dict = defaultdict()
    for k in dict_a.keys() | dict_b.keys():
        res_dict[k] = defaultdict()
        if k in dict_a and k not in dict_b:
            res_dict[k] = dict_a[k]
        elif k in dict_b and k not in dict_a:
            res_dict[k] = dict_b[k]
        else:
            res_dict[k].update(dict_a[k])
            res_dict[k].update(dict_b[k])

    return res_dict
