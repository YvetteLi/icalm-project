from altair import selection

from backend.kg_building_util import *
from backend.functionality_util import toml_load, run_query
from langchain.schema import Document
from neo4j_config.config import graph
from langchain_config.config import embedding_model
import logging
from langchain_community.graphs.graph_document import GraphDocument

# Setting up path for examples
EXAMPLE_PATH = 'assets/examples/example.toml'

def get_node_embeddings(text: str):
    # Generate embeddings for the node using the OpenAI Embeddings API
    return embedding_model.embed_query(text)


def extract_and_store_graph(
        document: Document,
        topic,
        first_time_load=True
) -> None:
    example_file = toml_load(EXAMPLE_PATH)
    # selected_example = example_file.get(topic, '')
    selected_example = example_file.get(topic, {})
    example = selected_example.get('example', '' )
    results = selected_example.get('results', '')

    # Extract graph data using OpenAI functions
    extract_chain = get_extraction_chain(example, results)
    logging.warning(extract_chain)

    data = extract_chain.invoke(document.page_content)['function']
    # Generate and store embeddings for each node
    for node in data.nodes:
        # Get the node embedding
        node_text = "question: " + node.properties[0].value + "answer" + node.properties[
            1].value  # Assuming `name` is the node's text description
        embedding = get_node_embeddings(node_text)

        # Store the node with its embedding
        node.properties.append(Property(key='embedding', value=embedding))
        # print (node)

    # Construct a graph document with the nodes containing embeddings
    graph_document = GraphDocument(
        nodes=[map_to_base_node(node) for node in data.nodes],
        relationships=[map_to_base_relationship(rel) for rel in data.rels],
        source=document
    )
    if first_time_load:
        graph.query("MATCH (n) DETACH DELETE n")
    graph.add_graph_documents([graph_document])
