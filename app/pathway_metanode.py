from random import random

from numpy.distutils.misc_util import blue_text
from pyvis.network import Network
import networkx as nx
from backend.functionality_util import *
import logging
import streamlit as st
from backend.find_learning_path import *
from backend.ask_question import answer_student_question


"""
This section get flashcards from the card with the highest entropy level
The same as  AI guided pathway and same as start from fundamental, as
the key topic of the flashcard has the highest entropy
"""


@st.cache_resource
def query_flashcard(batch_size=1, logging=logging):
    study_path = walk_with_entropy(
        k=batch_size,
        visited_nodes=set(st.session_state['explored']),
        starting_node_id='', logging=logging)
    return study_path

def recover_learning_path(flashcard_id):
    flashcard_id_str = "'" + "', '".join(map(str, flashcard_id)) + "'"
    logging.warning(f'input flashcard is {flashcard_id_str}')
    query = f"""
         MATCH (q1:Flashcard)
         WHERE q1.id IN [{flashcard_id_str}] 
         RETURN q1.question AS question, q1.answer AS answer, q1.id as id
        """
    logging.warning(f"query is {query}")
    result = run_query(query)
    return result


@st.fragment
def start_from_metanode(st, llm, batch_size=3):
    # Initialize session state variables
    current_batch = st.session_state.get('current_batch', 1)
    index = st.session_state['current_flashcard_index']

    start_idx = (current_batch - 1) * batch_size
    end_idx = current_batch * batch_size  # Ensure end_idx doesn't overflow

    # Fetch flashcards that have not been explored yet
    if st.session_state.get('rerun_query', True):
        flashcard_ids = list(query_flashcard(batch_size, logging))
        logging.warning(f"flashcards {flashcard_ids}, with size {len(flashcard_ids)}")
        # recover the flashcard with flashcard id, due to the previous calculation step is intense
        flashcards = recover_learning_path(flashcard_ids)
        logging.warning(f"results {flashcards}")
        st.session_state['rerun_query'] = False
        st.session_state['learning_path'] = flashcards
    else:
        flashcards = st.session_state['learning_path']

    # flashcards = list(query_flashcard(batch_size, logging))
    if len(flashcards) == 0:
        st.session_state['learning_finished'] = True
        return

    logging.warning(f"the current flashcard is {index}")

    flashcard = flashcards[start_idx+index]
    # flashcard = query_one_node_with_id(flashcard_id)
    #
    logging.warning(f"The flashcard being explored is {flashcard}")
    display_learning_path(st, explored_flashcards=st.session_state['explored'],
                                      mistake_cards=[card['id'] for card in st.session_state['mistake_card']],
                                      learning_path=flashcards[start_idx:min(end_idx, len(flashcards))])



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
        logging.warning(f"the current flashcard explored are {st.session_state['explored']}")
        # Increment the current flashcard index and reload to show next flashcard
        st.session_state['current_flashcard_index'] += 1
        if st.session_state['current_flashcard_index'] >= batch_size:
            # st.session_state["rerun_query"] = True
            st.session_state['current_batch'] = current_batch + 1
            logging.warning("refreshing the card search now")
            st.session_state['current_flashcard_index'] = 0
            # flashcards = query_flashcard(batch_size, logging)

            st.cache_resource.clear()
        st.rerun(scope="fragment")

    st.progress(len(st.session_state['explored']) / st.session_state['total_cards'])
    st.write(f"You've explored {len(st.session_state['explored'])} flashcards.")
    st.write(f"You've explored {len(st.session_state['explored'])} flashcards.")
    st.write(f"You've got {len(st.session_state['mistake_card'])} cards wrong.")

