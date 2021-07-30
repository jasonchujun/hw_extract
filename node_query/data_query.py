# Date  : 2021/7/26 17:33
# Author: ehzujnu
# File  : data_query.py
from py2neo import Graph, Node, Relationship, Subgraph

# match(a:part{name:'C771A0M0M1'})-[]->(b:port{name:'1'})-[c:CONNECT]->(d)<-[]-(e:part) return a,b,d,e
# match (n) detach delete n
# drop constraint on (p:part) assert p.part_name is unique
# drop index on :port(PIN_NUMBER)
