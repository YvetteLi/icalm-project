import streamlit as st
from langchain_config.config import llm


def anwer_student_question_prompt(flashcard, student_question):
    # Generate more examples using the LLM when not enough examples are found
    prompt = f"""
    You are a helpful teaching assistant. The user has made a mistake while answer the following question.

    The flashcard has the following information:
    - Flashcard Question: {flashcard['question']}
    - Flashcard Answer: {flashcard['answer']}

    The student asked you the following question
    - Student's question: {student_question}
    In this answer, we are allowed to use both information in the previous cards of {st.session_state.get('explored', [])}, as well as prior knowledge. 
   However, when new evidence conflicts with prior knowledge, we should trust the new evidence. 
   If the previous knowledge is not sufficient, We may not be able to answer the question. 
    """

    response = llm.predict(prompt).strip('\n')

    return response


@st.dialog("Ask a Question")
def answer_student_question(flashcard):
    student_question = st.text_input("Ask a question about the current flashcard")
    if st.button("Ask Intelligent Tutor for more details"):
        response = anwer_student_question_prompt(flashcard, student_question)
        st.write(f"Question: {flashcard['question']}.")
        st.write(f"Your Question: {student_question}")
        st.write(f"Response: {response}")
        st.cache_resource.clear()
