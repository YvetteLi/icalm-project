# ICALM: Interactive-Constructive-Active Learning Machine

## Proposal 
[Knowledge Graph based Recommendation System in EdTech](Knowledge_Graph_based_Recommendation_System.pdf)

## Poster
[EdTech Project.pdf](https://github.com/YvetteLi/icalm-project/blob/main/EdTech%20Project.pdf)

## Overview
The **Interactive-Constructive-Active Learning Machine (ICALM)** is an advanced Intelligent Tutoring System (ITS) designed to address challenges in student engagement and cognitive development in the era of Large Language Models (LLMs) like ChatGPT. ICALM integrates three key components:
1. **Concept Map Generation**: Converts flashcards into structured concept maps.
2. **Knowledge-Graph-Based Recommendations**: Encourages exploration of course topics through an interconnected knowledge graph.
3. **LLM-Facilitated Active Learning**: Supports active learning through chatbot interactions, personalized feedback, and reflective essay writing.

The system leverages the ICAP Framework to promote various levels of student engagement, from passive to interactive learning.

## Features
1. **Flashcard-to-Knowledge Graph Conversion**: Extracts relationships between concepts and organizes them into an interactive knowledge graph.
2. **Recommender System**: Suggests relevant topics based on user preferences and knowledge graph structure.
3. **Active Learning Support**: Facilitates reflection through LLM-powered essays, promoting deeper understanding.

## Educational Approach
ICALM is grounded in research on student engagement and cognitive development, particularly for students transitioning to higher education. By utilizing concept mapping, the system aids in making complex information more digestible and improving student comprehension.

### Core Components
1. **Entity-Relation Extraction**: Converts raw flashcard data into concept maps using KnowGL.
2. **Graph-Based Recommender System**: Provides intelligent topic suggestions based on academic content.
3. **Interactive Chatbot**: Students can engage in discussions with a chatbot to reinforce concepts and verify their understanding.
4. **Reflection Session**: Post-learning reflection essays are compared with summaries generated by LLMs for feedback.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YvetteLi/icalm-project.git
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables for OpenAI and Neo4j:
   ```bash
   export OPENAI_API_KEY=<your_openai_key>
   export NEO4J_URL=<neo4j_url>
   export NEO4J_USERNAME=<neo4j_username>
   export NEO4J_PASSWORD=<neo4j_password>
   ```

## Usage
1. **Uploading Flashcards**: Upload flashcards in text format to generate a knowledge graph.
2. **Choosing a Pathway**: Select a learning pathway, such as random flashcards or interest-based exploration.
3. **Review Mistakes**: Analyze incorrect answers and explore related concepts.

## Research Basis
ICALM's foundation lies in educational psychology, cognitive development, and learning sciences. It aims to bridge the gap between passive content absorption and active knowledge engagement, following the ICAP Framework.

## Summary of the Main Features:

### **Session State in `main.py`**
   - **Session Management**: The system maintains several states, such as:
     - `explored`: Flashcards already explored by the user.
     - `mistake_card`: Cards answered incorrectly.
     - `learning_finished`: Tracks when the learning process is complete.
     - These session variables ensure personalized learning progression and keep track of student performance across sessions.


### **Flashcard Uploading (`upload_flashcards`)**
   - **Purpose**: Provides an interface for users to upload flashcards, either through text files or from a pre-existing database.
   - **Features**:
     - Users can upload a flashcard file, which is processed and split into manageable chunks for building a knowledge graph.
     - If no file is uploaded, flashcards can be loaded from a database.
     - If custom content is entered, the system will build a knowledge graph based on that input.
   - **Key Functionality**:
     - Text from flashcards is split into smaller chunks using the `LineTextSplitter` class.
     - Each chunk is passed to `extract_and_store_graph` to build a knowledge dataset.
     - Flashcards can also be pulled from a predefined set in the `assets/flashcards` directory.

#### **LineTextSplitter Class**:
   - **Purpose**: Splits large blocks of text (flashcards) into smaller chunks to better handle and analyze them.
   - **Attributes**:
     - `chunk_size`: Defines the maximum number of lines per chunk.
     - `chunk_overlap`: Determines how much overlap there should be between chunks, helping to ensure context isn't lost between splits.
   - **Methods**:
     - `split_text()`: Breaks the text into chunks based on lines.
     - `split_documents()`: Breaks down documents into smaller chunks and returns them as new document objects.

#### **Knowledge Graph Building (`extract_and_store_graph`)**
   - **Purpose**: Builds a knowledge graph from the processed flashcards, integrating relationships between them.
   - **Steps**:
     - Loads examples and results from a configuration file.
     - Calls the `get_extraction_chain` function to extract graph data using OpenAI functions.
     - Filters nodes with relevant content and adds node embeddings.
     - Stores the extracted nodes and relationships in a graph database (Neo4j).
     - If it's the first time loading data, it clears the existing graph database before adding new data.

### Pathway Selections

   1. **Random Flashcard Pathway**:
      - **Main Feature**: Students explore flashcards randomly from the database, which are unvisited to avoid repetition.
      - **Correlation**: This pathway promotes **Active learning** by encouraging students to engage with new information, similar to how ICALM’s knowledge graph exposes students to novel topics.

   2. **Metanode-Based Pathway**:
      - **Main Feature**: Prioritizes flashcards related to concepts with high entropy, highlighting complex or interconnected ideas.
      - **Correlation**: Aligns with **Constructive learning** in ICALM by helping students understand and form connections between abstract concepts, fostering deeper cognitive engagement.
      - The following series of node and edge graphs illustrates the process of the MetaNode Pathway, where the system prioritizes nodes with the highest entropy, helping students build structured knowledge by exploring interconnected concepts ([Rossiello et al., 2022](https://arxiv.org/abs/2206.02315)).

#### Step 1: Initial Step - High Entropy Node Selection

The system starts by selecting the node (flashcard) with the highest entropy (the most interconnections).

```
  A --> B
  A --> C
  B --> D
  C --> E
```

Here, node **A** is selected because it has the highest entropy (most interconnections).

#### Step 2: Traversing to Neighboring Nodes

Once the high-entropy node is selected, the system traverses its neighboring nodes based on their entropy values.

```
  A --> B (selected)
  A --> C (selected)
  B --> D
  C --> E
```

Nodes **B** and **C** are visited after node **A** based on their entropy values.

#### Step 3: Exhausting Neighbors and Selecting a New Node

If the neighbors of the current node are exhausted, the system uses cosine similarity to find a new high-entropy node to explore.

```
  A --> B
  A --> C
  B --> D
  C --> E
  D --> F (new high-entropy node selected)
```

In this step, node **F** is selected using cosine similarity after exploring all neighboring nodes of the initial high-entropy node.


   3. **Interest-Based Pathway**:
      - **Main Feature**: Uses student input to recommend flashcards, prioritizing topics of interest using cosine similarity to match content with user preferences.
      - **Correlation**: This pathway embodies **Interactive learning**, allowing students to actively shape their learning process, similar to how ICALM facilitates learning based on students' evolving interests.
      - In the Interest-Based Pathway of ICALM, students input areas of interest, and the system matches relevant nodes using cosine similarity. This pathway encourages **interactive learning** through personalized, dynamic exploration ([Chi et al., 2012](https://doi.org/10.3102/0034654312449406)).

```
Student Input --> A (cosine similarity)
Student Input --> B (cosine similarity)
Student Input --> C (cosine similarity)
A --> Visited D
C --> Visited E
```

By embedding student input with a pre-trained language model and matching it to flashcards via cosine similarity, ICALM offers personalized learning paths.

#### Additional Functions that Apply to Each Pathways
   1. **Review Mistakes (`review_mistakes.py`)**
      - **Purpose**: Allows users to review flashcards they answered incorrectly.
      - **Key Functions**:
        - `generate_flashcard_with_llm()`: Uses an LLM to generate new flashcards based on the user's mistakes.
        - `generate_related_questions()`: Finds or generates flashcards related to the user’s incorrect answers.
        - Mistakes are stored and reviewed to reinforce learning.
   2. **Results Check (`results_check()`)**
      - **Purpose**: Queries the database to count the number of flashcards present.
      - **Error Handling**: If any issues arise during query execution, it displays an error message and stops the process.
      - **Interactive Graph**: Calls `interactive_graph` to display visual information regarding the flashcards.

   3. **Additional Utilities**
      - `interactive_graph()`: Displays flashcards and their relationships visually using a graph layout.
      - `check_answer()`: Compares a student's answer to the correct answer and provides feedback based on similarity.
      - `get_node_embeddings()`: Generates embeddings for nodes using a language model.


### Correlation with Your Proposal:
- The **ICAP framework** underpins these pathways, as they correspond to different levels of cognitive engagement—**active** (random flashcards), **constructive** (metanode-based learning), and **interactive** (interest-based learning).
- ICALM’s recommendation system aligns closely with the **knowledge-graph** and **concept-mapping** methods in these pathways, providing structure for deeper student learning and engagement with complex academic materials.
- This system addresses academic preparedness by offering personalized and dynamic learning experiences that help students develop essential cognitive and comprehension skills, particularly for higher education readiness.

By incorporating flashcards, knowledge graphs, and personalized pathways, ICALM can effectively bridge gaps in student comprehension and academic preparedness, resonating with your goals of enhancing student learning and engagement.


## Future Work
- Integration with additional AI models for deeper personalization.
- Expansion to support a broader range of subjects.

## License
This project is licensed under the CC0-1.0 license. See the [LICENSE](LICENSE) file for details.

