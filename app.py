# Date  : 2021/7/7 13:36
# Author: ehzujnu
# File  : app.py
from config import Config
from flask import Flask, render_template, request, flash, redirect, url_for, session, g
from py2neo import Graph, Node, Relationship, Subgraph

app = Flask(__name__)
graph = Graph("http://localhost:7474", auth=(Config.neo4j_username, Config.neo4j_password))


@app.route('/')
def index():
    request.get()
    return render_template("")


if __name__ == '__main__':
    app.run(port=8080)
