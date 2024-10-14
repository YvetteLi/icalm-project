import logging
from backend.functionality_util import run_query


# TODO: Student may want to switch to a new node anytime, then we need to recalculate the order of visited nodes
def get_node_with_highest_entropy():
    query = """
    MATCH (n)-[r]->()
    WITH n, type(r) AS relType, count(r) AS relCount, COUNT { (n)--() } AS totalRels
    WITH n, (relCount * 1.0 / totalRels) AS p
    RETURN n, -sum(p * log(p) / log(2)) AS entropy
    ORDER BY entropy DESC
    LIMIT 1
    """
    result = run_query(query)
    if result:
        return result[0]['n']  # Return the node with the highest entropy
    return None


def get_neighbors_with_entropy(node_id):
    query = f"""
        MATCH (n)-[r]->(neighbor)
        WHERE n.id = '{node_id}'
        WITH neighbor, type(r) AS relType, count(r) AS relCount, COUNT {{ (neighbor)--() }} AS totalRels
        WITH neighbor, (relCount * 1.0 / totalRels) AS p
        RETURN neighbor, -sum(p * log(p) / log(2)) AS entropy
        ORDER BY entropy DESC
    """
    return run_query(query)


def find_closest_node_with_high_entropy(visited_nodes, k=1):
    visited_nodes_str = "'" + "', '".join(map(str, visited_nodes)) + "'"
    # Use Neo4j Graph Data Science API to find the K-nearest neighbors
    cosine_query = f"""
        MATCH (q1:Flashcard), (q2:Flashcard)
        WHERE NOT q1.id IN [{visited_nodes_str}] 
        AND NOT q2.id IN [{visited_nodes_str}]
        AND q1 <> q2
        WITH q1, q2, gds.similarity.cosine(q1.embedding, q2.embedding) AS similarity
        RETURN q1 as node1, q2 as node2, similarity
        ORDER BY similarity DESC
        LIMIT {k}
        """
    # print (cosine_query)
    result = run_query(cosine_query)
    if result:
        # Return the closest node that has not been visited yet
        return result[0]['node2'] if result[0]['node1'] in visited_nodes else result[0]['node1']
    return None

def query_one_node_with_id(flashcard_id):
    query = f"""
    MATCH (q:Flashcard)
    WHERE NOT q.id = '{flashcard_id}' 
    RETURN q as node
    """
    node = run_query(query)[0]['node']
    logging.info(f"node retrieved is {node.id}")
    return node

def walk_with_entropy(k=3, visited_nodes=set(), starting_node_id='', logging=logging):
    # Step 1: Find the node with the highest entropy

    if not starting_node_id:
        logging.info("Start from getting the node with highest entropy")
        node = get_node_with_highest_entropy()
        if not node:
            logging.error("No starting node found.")
            return visited_nodes
    else:
        node = query_one_node_with_id(starting_node_id)
    visited_nodes.add(node['id'])

    while True:
        # Step 2: Get neighbors and walk based on entropy
        neighbors = get_neighbors_with_entropy(node['id'])
        if neighbors:
            for neighbor in neighbors:
                if neighbor['neighbor']['id'] not in visited_nodes:
                    logging.info(f"Moving to node: {neighbor['neighbor']['id']} with entropy: {neighbor['entropy']}")
                    visited_nodes.add(neighbor['neighbor']['id'])
                    node = neighbor['neighbor']  # Move to the neighbor node
                    break
            else:
                logging.info(f"Exhausted neighbors for node {node['id']}")
                # Step 4: If the neighborhood is exhausted, use KNN to find the next closest node with high entropy
                visited_ids = [visited_node["id"] for visited_node in visited_nodes]
                next_node = find_closest_node_with_high_entropy(visited_ids, k)
                if next_node:
                    logging.info(f"Moving to closest node: {next_node['id']} with high entropy.")
                    node = next_node
                    visited_nodes.add(next_node['id'])
                else:
                    logging.info("No more nodes to visit.")
                    break
        else:
            logging.info(f"Exhausted neighbors for node {node['id']}")
            next_node = find_closest_node_with_high_entropy(visited_nodes, k)
            if next_node:
                logging.info(f"Moving to closest node: {next_node['id']} with high entropy.")
                node = next_node
                visited_nodes.add(next_node['id'])
            else:
                logging.info("No more nodes to visit.")
                break
    return visited_nodes

