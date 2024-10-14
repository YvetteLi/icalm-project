from upload_flashcards import upload_flashcards
from langchain_config.config import llm
from backend.review_mistakes import review_mistakes, render_mistake_card
from pyvis.network import Network


# main.py
import streamlit as st
import pathway_random
import pathway_interest
import pathway_metanode
#
if 'explored' not in st.session_state:
    st.session_state['explored'] = []
if 'current_flashcard_index' not in st.session_state:
    st.session_state['current_flashcard_index'] = 0
if "mistake_card" not in st.session_state:
    st.session_state["mistake_card"] = []
if "learning_finished" not in st.session_state:
    st.session_state['learning_finished'] = False
if "total_cards" not in st.session_state:
    st.session_state['total_cards'] = 50
st.session_state['current_batch'] = 1

def main():
    st.title("Intelligent Tutoring System")

    st.header("Step 1: Upload Flashcards")
    upload_flashcards()

    pathway = st.sidebar.selectbox(
        "Choose a learning pathway:",
        [
            "Select Pathway",  # Placeholder option to force the user to select a real option
            "Start from Random Flashcard",
            "Start Based on Student Interest",
            "Guided Path Based on Fundamental Concept"
        ]
    )

    # Set session state to True if a valid pathway is selected
    if pathway != "Select Pathway":
        st.session_state['path_selected'] = True
    else:
        st.session_state['path_selected'] = False

    # Show Step 2 only after a valid pathway has been selected
    if st.session_state['path_selected']:
        st.title("Step 2: Explore Flashcards through Different Pathways")

        # Pathway selection logic
        if pathway == "Start from Random Flashcard":
            pathway_random.start_from_random(st, llm)
        elif pathway == "Start Based on Student Interest":
            pathway_interest.start_from_student_interest(st, llm)
        elif pathway == "Guided Path Based on Fundamental Concept":
            pathway_metanode.start_from_metanode(st, llm)

        # Mistake Review Sidebar
        st.sidebar.header("Mistake Review")
        if st.sidebar.button("Review Mistakes"):
            flashcard_set = review_mistakes(st)
            render_mistake_card(st, flashcard_set)
    else:
        st.info("Please select a learning pathway to proceed to Step 2.")


if __name__ == "__main__":
    main()
