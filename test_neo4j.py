# Date  : 2021/7/5 14:12
# Author: ehzujnu
# File  : test_neo4j.py
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Zhujunpwd1989$"))


def add_friend(tx, name, friend_name):
    tx.run("MERGE (a:Person {name: $name}) " "MERGE (a)-[:KNOWS]->(friend:Person {name: $friend_name})",
           name=name, friend_name=friend_name)


def print_friends(tx, name):
    for record in tx.run("MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
                         "RETURN friend.name ORDER BY friend.name", name=name):
        print(record["friend.name"])


def add_part_and_port(tx, CQL_string):
    tx.run(CQL_string)


with driver.session() as session:
    session.read_transaction(print_friends)
