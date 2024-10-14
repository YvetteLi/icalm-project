from backend.functionality_util import *
import logging
import streamlit as st
from backend.ask_question import answer_student_question
from langchain_config.config import embedding_model
from langchain_config.config import llm

"""
This section get flashcards from students interests. Graph will automatically
extract the key concept from students' natural language input and query data 
automatically
"""


@st.cache_resource
def get_student_interest(student_input, visited_nodes, batch_size=10):
    """
    Caches the resource to retrieve student interest flashcards based on input and visited nodes.

    Args:
        student_input (str): The current input from the student.
        visited_nodes (list): A list of flashcard IDs already visited by the student.
        batch_size (int, optional): The number of flashcards to retrieve. Defaults to 10.

    Returns:
        list: A list of flashcards (each represented by a dictionary) containing 'question', 'answer', and 'id' keys.
    """
    student_input_embedded = embedding_model.embed_query(student_input)
    visited_nodes_str = "'" + "', '".join(map(str, visited_nodes)) + "'"
    # Use Neo4j Graph Data Science API to find the K-nearest neighbors
    cosine_query = f"""
         MATCH (q1:Flashcard)
         WHERE NOT q1.id IN [{visited_nodes_str}] 
         WITH q1, gds.similarity.cosine(q1.embedding, {student_input_embedded}) AS similarity
         RETURN q1.question AS question, q1.answer AS answer, q1.id as id
         ORDER BY similarity DESC
         LIMIT {batch_size}
         """
    flashcards = run_query(cosine_query)
    logging.warning(f"the flashcards queried are {flashcards}")
    if len(flashcards) == 0:
        st.write("You've learned all the flashcards")
        return []
    return flashcards

def get_all_metanodes():
    """
    Fetches all distinct metanode names from the database, stripping the "metanode" suffix.

    Returns:
        list: A list of metanode names with the "metanode" suffix removed.
    """
    query = """
        MATCH (m:Metanode)
        RETURN DISTINCT m.name AS metanode_name
    """
    metanodes = run_query(query)
    # removing the " metanode" suffix
    if len(metanodes) > 0:
        metanode_name = [record.value().rsplit(' ', 2)[0] for record in metanodes]
        return metanode_name
    else:
        return []

@st.fragment
def start_from_student_interest(st, llm, batch_size=10, lookback_size=10):
    """
    start_from_student_interest

    Initializes the learning session based on the student's interest and interaction with flashcards.
    1. **Graph Structure**:
       - We assume that MetaNodes (e.g., broad categories like "Economics", "Biology") are connected to flashcards in a graph. Each flashcard belongs to a MetaNode.
       - MetaNodes will have relationships to flashcards, and flashcards can be compared for similarity using cosine similarity in Neo4j.
    2. **Process Flow**:
       - Step 1: Show available MetaNodes and ask students to choose one.
       - Step 2: Once selected, show flashcards related to that MetaNode.
       - Step 3: If all flashcards in a MetaNode are explored, show the remaining MetaNodes.
       - Step 4: If all MetaNodes are explored but flashcards remain, use cosine similarity to recommend the most relevant flashcard.

    st: Streamlit object
        The Streamlit object for handling UI components and session states.
    llm: Language model object
        The language model used for generating hints and processing student answers.
    batch_size: int, optional
        The number of flashcards to fetch in one batch (default is 10).
    lookback_size: int, optional
        The number of previously explored questions to consider for avoiding repetition (default is 10).
    """
    # Initialize session state variables
    # Fetch flashcards that have not been explored yet

    # Iterate through the flashcards and display them
    # flashcards = query_flashcard(batch_size, logging)
    index = st.session_state['current_flashcard_index']
    logging.warning(f"current index is {index}")

    student_question = st.text_input("Please enter your questions regarding this topic")
    available_metanodes = get_all_metanodes()
    selected_metanode = []
    if available_metanodes:
        selected_metanode.extend(st.multiselect("Select a pathway to explore", available_metanodes))
    # Check if the input box has been filled
    logging.warning(f"student_question {student_question}, selected_metanode {selected_metanode} ")
    if student_question != '':
        st.session_state['input_provided'] = True  # Set the flag to True when input is provided
    else:
        st.warning("Please enter your question to proceed.")

    # Proceed only if input is provided
    if st.session_state.get('input_provided', False):
        question_query = student_question + ". I am interested in the following topics: " + ', '.join(selected_metanode)
        questions_explored = st.session_state["explored"]

        if st.session_state.get('rerun_query', True):
            flashcards = get_student_interest(question_query,
                                 visited_nodes=set(questions_explored[max(0, len(questions_explored) - lookback_size):]),
                                 batch_size=batch_size)
            st.session_state['rerun_query'] = False
            st.session_state['learning_path'] = flashcards
        else:
            flashcards = st.session_state['learning_path']

        if len(flashcards) == 0:
            st.session_state['learning_finished'] = True
            return

        flashcard = flashcards[index]

        # logging.warning(f"mistake_Cards = {[card['id'] for card in st.session_state['mistake_card']]}")
        # logging.warning(f"explored_flashcards = {st.session_state['explored']}")
        # logging.warning(f"flashcard {flashcards}")
        display_learning_path(st, explored_flashcards=st.session_state['explored'],
                              mistake_cards=[card['id'] for card in st.session_state['mistake_card']],
                              learning_path=flashcards)

        # for flashcard in flashcards:
        st.subheader(f"Question: {flashcard['question']}")
        student_answer = st.text_input(f"Your answer for flashcard {flashcard['id']}:")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Submit Answer"):
                check_answer(st, student_answer, flashcard, logging)

            if st.button("Show Hint"):
                getting_hint(st, llm, flashcard, logging)

            if st.button("Show Answer"):
                st.write(f"The correct answer is {flashcard['answer']}")

        st.markdown("<br>", unsafe_allow_html=True)
        with col2:
            if st.button("Explore this Flashcard"):
                answer_student_question(flashcard)

            if st.button("Add to Mistake List"):
                modified_flashcard = dict(flashcard)
                modified_flashcard["wrong_answer"] = student_answer
                logging.warning(f"Adding to mistake list with {modified_flashcard}")
                st.session_state["mistake_card"].append(modified_flashcard)
                st.write(f"This card {modified_flashcard['id']} has been added to Mistake List")
                # logging.warning(f"current session state after adding mistake {st.session_state['mistake_card']}")

        # Button to mark as explored
        if st.button(f"Next Question and Mark the Question Explored"):
            # Add flashcard to explored list
            st.session_state['explored'].append(flashcard['id'])
            # Increment the current flashcard index and reload to show next flashcard
            st.session_state['current_flashcard_index'] += 1
            if st.session_state['current_flashcard_index'] >= len(flashcards):
                st.session_state["rerun_query"] = True
                logging.warning("refreshing the card search now")
                st.session_state['current_flashcard_index'] = 0
                # questions_explored = st.session_state["explored"]
                # flashcards = get_student_interest(question_query,
                #                                   visited_nodes=set(
                #                                       questions_explored[max(0, len(questions_explored) - lookback_size):]),
                #                                   batch_size=batch_size)

                st.cache_resource.clear()
            st.rerun(scope="fragment")

        st.progress(len(st.session_state['explored'])/st.session_state['total_cards'])
        st.write(f"You've explored  {','.join(st.session_state['explored'])} ")
        st.write(f"You've explored {len(st.session_state['explored'])} flashcards.")
        st.write(f"You've got {len(st.session_state['mistake_card'])} cards wrong.")
