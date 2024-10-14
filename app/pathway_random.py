# pathway_random.py
from requests import session

from backend.functionality_util import *
import logging
import streamlit as st
from backend.ask_question import answer_student_question


@st.cache_resource
def query_flashcard(batch_size=1, logging=logging):
    query = f'''
    MATCH (f:Flashcard)
    WITH f, rand() AS randomValue
    WHERE NOT f.id IN {st.session_state.get('explored', [])}
    RETURN f.question AS question, f.answer AS answer, f.id as id
    ORDER BY randomValue
    LIMIT {batch_size}
    '''
    flashcards = run_query(query)
    logging.warning(f"queried flashcard is {flashcards}")
    if len(flashcards) == 0:
        st.write("You've learned all the flashcards!")
        return []
    # output = {"stored_flashcards": flashcards}
    return flashcards

@st.fragment
def start_from_random(st, llm, batch_size=1):
    # Initialize session state variables
    # Fetch flashcards that have not been explored yet

    # Iterate through the flashcards and display them
    # flashcards = query_flashcard(batch_size, logging)
    index = st.session_state['current_flashcard_index']
    logging.warning(f"current index is {index}")
    flashcards = query_flashcard(batch_size, logging)
    if len(flashcards) == 0:
        st.session_state['learning_finished'] = True
        return
    flashcard = flashcards[index]

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
            logging.warning("refreshing the card search now")
            st.session_state['current_flashcard_index'] = 0
            flashcards = query_flashcard(batch_size, logging)

        st.cache_resource.clear()
        st.rerun(scope="fragment")

    st.write(f"You've explored  {st.session_state['explored']} ")
    st.write(f"You've explored {len(st.session_state['explored'])} flashcards.")
    st.write(f"You've got these flashcards {len(st.session_state['mistake_card'])} wrong.")
