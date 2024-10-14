import os

from neo4j import GraphDatabase
from langchain.graphs import Neo4jGraph
from dotenv import load_dotenv

load_dotenv()
# Neo4j connection configuration
url = os.getenv('NEO4J_URL') # neo4j+s://2794d51e.databases.neo4j.io
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD') # K0_cDvQ5_tPjK0l1zlj3xAcY8LNr4pwbNh1nx2EZrwI


# Setup Neo4j connection
def get_graph_driver(url, username, password):
    graph = Neo4jGraph(
    url=url,
    username=username,
    password=password
)
    return graph

# Get Neo4j driver
graph = get_graph_driver(url, username, password)
