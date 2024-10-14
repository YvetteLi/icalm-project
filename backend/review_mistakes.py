import json

import streamlit as st
from backend.functionality_util import run_query
from langchain_config.config import llm
import logging

def generate_flashcard_with_llm(flashcard, num_cards=1):
    prompt = f"""
    You are a helpful teaching assistant. The user has made a mistake while answer the following question.
    
    The flashcard has the following information:
    - Flashcard Question: {flashcard['question']}
    - Flashcard Answer: {flashcard['answer']}
    - Student Answer: {flashcard.get("wrong_answer", "")}

    Flashcard must fit the theme {flashcard['id']}
    Provide a helpful and concise hint or explanation related to this flashcard.
    the out put should be in a json parsable format that include {num_cards} cards that follow the format
    
    [OUTPUT]
    - flashcard: 
      - id: [Extract the topic of this new generated flashcard]
        label: "Flashcard"
        properties:
          question: [Flashcard question]
          answer: [Flashcard answer]
    """

    response = llm.predict(prompt)
    logging.warning(f"LLM Response {response}")
    try:
        results = json.loads(response)
    except Exception as e:
        logging.warning("JSON could not load llm response")
        results = []
        for line in response.split("\n", 2):
            question = line.split('question:')[1].split('answer:')[0].strip()
            answer = line.split('answer:')[1].strip()
            results.append({"question": question, "answer": answer})

    # Return the generated question and answer as a new flashcard
    return results


def generate_related_questions(flashcard, num_cards=1):
    # Query the knowledge graph to get related information (e.g., 3 relevant nodes)
    related_query = f'''
    MATCH (f:Flashcard)-[r]-(f2:Flashcard)
    WHERE f.id = "{flashcard['id']}"
    RETURN f2.id AS related_id, f2.question AS question, f2.answer AS answer, r.type AS relationship
    '''
    related_nodes = run_query(related_query)
    if related_nodes and len(related_nodes) > num_cards:
        logging.warning(related_nodes)
        return [flashcard for flashcard in related_nodes[:num_cards]]
    else:
        logging.warning("using llm to generate similar nodes")
        if related_nodes:
            generated_cards_num = num_cards-len(related_nodes)
        else:
            generated_cards_num = num_cards
        generated_llm_cards = generate_flashcard_with_llm(flashcard, generated_cards_num)
        return generated_llm_cards

def review_mistakes(st, num_cards=3):
    flashcard_set = []
    if "mistake_card" in st.session_state and len(st.session_state["mistake_card"]) > 0:
        for mistake in st.session_state["mistake_card"]:
            # st.write(f"Question: {mistake['question']}")
            # st.write(f"Your answer: {mistake['wrong_answer']}")
            related_questions = generate_related_questions(mistake, num_cards)
            # st.write("Here are three more questions to test your knowledge:")
            flashcard_set.append({'mistake_card': mistake, 'flashcard': related_questions})
    else:
        st.info("No mistakes recorded yet.")
    return flashcard_set

@st.dialog("Review Your Mistakes")
def render_mistake_card(st, flashcard_deck):
    for card_set in flashcard_deck:
        mistake_card = card_set['mistake_card']
        extra_cards = card_set['flashcard']
        st.subheader(f"The Question you've got wrong is: {mistake_card['id']}")
        st.write(f"Question: {mistake_card['question']}.\n Answer: {mistake_card['answer']}")
        st.write(f"Your Answer was: {mistake_card.get('wrong_answer', 'Your answer is not available.')}")

        st.subheader(f"Other cards")
        st.write(f"With your mistake, we found some other flash cards that could be helpful for you.")
        # logging.warning(extra_cards)
        for key, extra_card in extra_cards.items():
            # logging.warning(extra_card)
            st.write(f"Question: {extra_card['properties']['question']}.")

        if st.button("Show Answer", key="mistake_answer"):
            for key, extra_card in extra_cards.items():
                st.write(f"Answer: {extra_card['properties']['answer']}")