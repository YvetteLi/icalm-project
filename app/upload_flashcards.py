import os

import streamlit as st
from io import StringIO

from backend.functionality_util import run_query, interactive_graph
from backend.knowledge_graph import extract_and_store_graph
from langchain.schema import Document
from langchain.text_splitter import TextSplitter


# Setting up path for examples
import logging
FLASHCARD_PATH = 'assets/flashcards'


class LineTextSplitter(TextSplitter):
    """
         class LineTextSplitter(TextSplitter):

         A class that inherits from TextSplitter and provides functionality
         to split text based on lines, respecting the provided chunk size and overlap.

         Attributes:
         chunk_size (int): The maximum number of lines per chunk.
         chunk_overlap (int): The number of overlapping lines between consecutive chunks.

         Methods:
         __init__(chunk_size, chunk_overlap=0):
             Initializes the LineTextSplitter with the given chunk size and overlap.

         split_text(text):
             Splits the given text into chunks based on lines.

         split_documents(documents):
             Splits the page content of each document in the given list into chunks.

         def __init__(self, chunk_size: int, chunk_overlap: int = 0):

         Initializes the LineTextSplitter with the specified chunk size and overlap.

         Parameters:
         chunk_size (int): The maximum number of lines per chunk.
         chunk_overlap (int): The number of overlapping lines between consecutive chunks. Default is 0.

         def split_text(self, text: str):

         Splits the provided text into chunks based on lines, respecting the chunk size and overlap.

         Parameters:
         text (str): The text to be split into chunks.

         Returns:
         list: A list of text chunks.

         def split_documents(self, documents):

         Splits the page content of each document in the provided list into chunks.

         Parameters:
         documents (list): A list of Document objects to be split.

         Returns:
         list: A list of Document objects, each containing a chunk of text.
    """
    def __init__(self, chunk_size: int, chunk_overlap: int = 0):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str):
        # Split text into lines
        lines = text.splitlines()

        # Chunk the text by lines, respecting chunk size and overlap
        chunks = []
        for i in range(0, len(lines), self.chunk_size - self.chunk_overlap):
            chunk_lines = lines[i:i + self.chunk_size]
            chunk = '\n'.join(chunk_lines)
            chunks.append(chunk)

        return chunks

    def split_documents(self, documents):
        # Split each document's text into chunks
        split_docs = []
        for document in documents:
            text_chunks = self.split_text(document.page_content)
            # Create a new Document for each chunk
            split_docs.extend([Document(page_content=chunk) for chunk in text_chunks])
        return split_docs

def results_check(selection=''):
    """
        results_check(selection='')

        This function executes a query to count the total number of flashcards in the database.
        It then updates the UI with the total number of flashcards found and sets the 'total_cards'
        value in the session state. If an error occurs during the execution of the query,
        an error message is displayed and the execution is stopped.

        Parameters:
        selection (str): An optional string to tailor the query or display messages.
    """
    query = """
        MATCH (f:Flashcard)
        RETURN COUNT(f) AS total_flashcards
        """
    try:
        result = run_query(query)[0]['total_flashcards']
        st.write(f"Finished loading for {selection} and in total {result} flashcards are found")
        st.session_state['total_cards'] = result
    except Exception as e:
        st.write(f"Problem occurred: {e}. Problem occurred with the flashcards writing")
        st.stop()

    interactive_graph(st, display_batch=50)


def upload_flashcards():
    """
    Allows the user to upload flashcards in text format, load from the database, or enter custom content to build a knowledge graph.

    upload_flashcards() handles three main options for the user:

    1. Uploading a flashcard file manually which will be processed and split into smaller chunks to build a knowledge graph.
    2. Loading flashcards from a pre-existing database if no file is uploaded.
    3. Entering custom content directly to build a knowledge graph.

    In case a file is uploaded:
    - The uploaded file is read and processed to extract content.
    - The content is split into smaller chunks using LineTextSplitter.
    - Each chunk is passed to the extract_and_store_graph function to build the knowledge dataset.

    If the user chooses to load from the database:
    - The content is retrieved from the specified path and split into smaller chunks.
    - Each chunk is then passed to the extract_and_store_graph function using the selected topic.

    If the user prefers to proceed without uploading or loading:
    - The function checks the results stored in the database.

    Parameters:
    None

    Returns:
    None
    """
    st.markdown("### Option 1: Upload your flashcards in text format.")

    # File uploader for manual upload
    uploaded_file = st.file_uploader("Choose a flashcard file", type="txt")

    # # Button to bypass the file upload and load from the database
    # bypass_db_button = st.button("Load from Database")

    # If a file is uploaded, process the file
    if uploaded_file is not None:
        content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        document = Document(page_content=content)
        topic = st.text_input("What is the topic of the content?")
        st.write("Building knowledge graph from text or flashcards...")
        text_splitter = LineTextSplitter(chunk_size=50, chunk_overlap=0)
        # Split the document into smaller chunks
        documents = text_splitter.split_documents([document])
        first_time_load = True
        for document in documents:
            # loading to the dataset
            extract_and_store_graph(document,
                                    topic=topic,
                                    first_time_load=first_time_load)  # Use the document from the uploaded file
        st.success("Knowledge graph built successfully from uploaded file.")
    # If the bypass button is clicked, load flashcards from the database
    # elif bypass_db_button:
    st.divider()  # Alternatively, you can use st.markdown("---") for a horizontal rule

    st.markdown("### Option 2: ...Or, Upload Your file")
    st.write("No file uploaded. Loading flashcards from the database...")
    flashcard_db = [f.split('.')[0].capitalize() for f in os.listdir(FLASHCARD_PATH)]
    with st.form("Select from database"):
        selection = st.selectbox(f"Choose one of the topics: ",
                                  flashcard_db)
        submitted = st.form_submit_button('Submit')
    # Convert your custom text into a LangChain document
    # logging.warning(f"Your choice {selections} has been submitted ")
    if submitted:
        # logging.warning(f"Your choice {selections} has been submitted ")
        st.write(f"Your choice {selection} has been submitted ")
        with open(f"{FLASHCARD_PATH}/{selection}.csv") as f:
            content_text = f.read()
        document = Document(page_content=content_text)
        # Define chunking strategy (splitting the text into manageable chunks)
        text_splitter = LineTextSplitter(chunk_size=35, chunk_overlap=0)

        # Split the document into smaller chunks
        documents = text_splitter.split_documents([document])
        first_time_load = True
        for doc in documents:
            logging.warning(doc.page_content)
            # loading to the dataset
            extract_and_store_graph(doc, topic=selection.lower(), first_time_load=first_time_load)
            first_time_load = False
        st.success(f"Knowledge graph for {selection} built successfully from the stored dataset.")
        results_check(selection=selection)

    st.divider()
    st.markdown("### Option 3: Enter Custom Content")

    if st.checkbox("Proceed without uploading or loading from the database"):
        results_check(selection='stored in database')

    # If neither file is uploaded nor the button is clicked, do nothing
    else:
        st.info("Please upload a file or load from the database.")
