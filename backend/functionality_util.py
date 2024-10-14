# utils.py
# imports for the graph network
import tomllib

from neo4j_config.config import graph
from fuzzywuzzy import fuzz
import logging
from pyvis.network import Network
import networkx as nx
# Function to run Cypher queries
# def run_query(query):
#     with graph.session() as session:
#         result = session.run(query)
#         return [record for record in result]

def run_query(query):
    result = graph.query(query)
    return result

# Interactive Graph Visualization using Pyvis
def interactive_graph(st, display_batch=50):
    st.header("Explore the Graph Visually")

    # Create a NetworkX graph
    G = nx.Graph()

    # Get nodes and relationships from the graph database
    query = f'''
    MATCH (f:Flashcard)-[r]->(f2:Flashcard)
    RETURN f.id AS from, f2.id AS to, r.type AS type
    LIMIT {display_batch}
    '''
    results = run_query(query)

    # Add nodes and edges to the graph
    for result in results:
        G.add_node(result['from'], label=result['from'])
        G.add_node(result['to'], label=result['to'])
        G.add_edge(result['from'], result['to'], label=result['type'])

    # Loading Single Nodes
    loaded_nodes = [node['from'] for node in results] + [node['to'] for node in results]
    query = f"""
    MATCH (f:Flashcard) 
    Where not f.id in {loaded_nodes}
    RETURN f.id As single_node
    LIMIT {display_batch}
    """
    results = run_query(query)
    for result in results:
        G.add_node(result['single_node'], label=result['single_node'])

    # Initialize Pyvis Network
    net = Network(notebook=False, height="750px", width="100%", directed=True)
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])

    # Display the network in Streamlit
    html_content = net.generate_html()
    # net.show(html_content)
    st.components.v1.html(html_content, height=750)


# Display Flashcard with Hint
def generate_hint_llm(llm, flashcard):
    # Check if related_id and relationship_type are present
    prompt = f"""
    You are a helpful assistant. The user has asked for a hint about the following flashcard, but there is no explicit relationship found.

    The flashcard has the following information:
    - Flashcard Question: {flashcard['question']}
    - Flashcard Answer: {flashcard['answer']}
    
    Flashcard must fit the theme {flashcard['id']}
    Provide a helpful and concise hint or explanation related to this flashcard.
    """

    # Call the LLM (OpenAI's GPT model in this example)
    response = llm.predict(prompt)

    return response.strip()


def getting_hint(st, llm, flashcard, logging):
    logging.warning("generating hints")
    # Query for related flashcards
    hint_query = f'''
    MATCH (f:Flashcard)-[r]->(f2:Flashcard)
    WHERE f.id = "{flashcard['id']}"
    RETURN r.type AS relationship, f2.id AS related_id
    LIMIT 1
    '''
    logging.warning("hint has been pressed")
    hint_data = run_query(hint_query)
    if not hint_data:
        logging.warning("generating from llm")
        st.write("No related flashcards found, using LLM to generate")
        hint = generate_hint_llm(llm, flashcard)
    else:
        logging.warning("Generating from other source")
        hint_data = hint_data[0]
        hint = f"This flashcard is related to {hint_data['related_id']}"
        if st.button("Generate another hint using LLM?", key=f"generate_hint"):
            hint = generate_hint_llm(llm, flashcard)
    st.write(f"{hint}")

def check_answer(st, student_answer, flashcard, logging):
    actual_answer = flashcard['answer'].strip().lower()  # Clean up the actual answer
    student_answer_cleaned = student_answer.strip().lower()  # Clean up the student's answer
    similarity = fuzz.ratio(student_answer_cleaned, actual_answer)

    # Set a similarity threshold (e.g., 80%)
    if similarity >= 80:
        st.write(f"Correct answer! Similarity score: {similarity}%")
    else:
        st.write(f"Incorrect! Similarity score: {similarity}%. The correct answer is: {flashcard['answer']}")

    logging.warning(f"Displayed flashcard {flashcard['id']}")


def toml_load(path):
    with open(path, 'rb') as f:
        return tomllib.load(f)


def display_learning_path(st, explored_flashcards, mistake_cards, learning_path):
    # Create a horizontal layout for the path
    # Create a horizontal layout for the path
    path_html = '''
    <div style="display: flex; align-items: center; justify-content: space-around;">
    '''

    for index, flashcard in enumerate(learning_path):
        # Use emojis for fun and clear visualization
        if flashcard['id'] in mistake_cards:
            # Red dot for mistakes
            path_html += f'<span style="font-size: 12px;">🔴{flashcard["id"]}</span>'
        elif flashcard['id'] in explored_flashcards:
            # Green dot for explored
            path_html += f'<span style="font-size: 12px;">🟢 {flashcard["id"]}</span>'
        else:
            # Gray dot for unexplored
            path_html += f'<span style="font-size: 12px;">⚪ </span>'

        # Add a short line to represent the relationship, except after the last flashcard
        if index < len(learning_path) - 1:
            path_html += '<span style="width: 50px; height: 2px; background-color: black; display: inline-block; margin: 0 10px;"></span>'

    path_html += '</div>'

    # # Display in Streamlit
    # st.markdown("### Learning Path:")
    st.markdown(path_html, unsafe_allow_html=True)

