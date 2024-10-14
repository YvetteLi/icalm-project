from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_structured_output_chain,
)
from langchain.prompts import ChatPromptTemplate
from langchain_config.config import llm

from langchain_community.graphs.graph_document import (
    Node as BaseNode,
    Relationship as BaseRelationship,
    GraphDocument,
)
from typing import List, Dict, Any, Optional
from langchain.pydantic_v1 import (Field, BaseModel)


#
class Property(BaseModel):
    """A single property consisting of key and value"""
    key: str = Field(..., description="key")
    value: Any = Field(..., description="value")


class Node(BaseNode):
    properties: Optional[List[Property]] = Field(
        None, description="List of node properties")


class Relationship(BaseRelationship):
    properties: Optional[List[Property]] = Field(
        None, description="List of relationship properties"
    )


class KnowledgeGraph(BaseModel):
    """Generate a knowledge graph with entities and relationships."""
    nodes: List[Node] = Field(
        ..., description="List of nodes in the knowledge graph")
    rels: List[Relationship] = Field(
        ..., description="List of relationships in the knowledge graph"
    )


def format_property_key(s: str) -> str:
    words = s.split()
    if not words:
        return s
    first_word = words[0].lower()
    capitalized_words = [word.capitalize() for word in words[1:]]
    return "".join([first_word] + capitalized_words)


def props_to_dict(props) -> dict:
    """Convert properties to a dictionary."""
    properties = {}
    if not props:
        return properties
    for p in props:
        properties[format_property_key(p.key)] = p.value
    return properties


def map_to_base_node(node: Node) -> BaseNode:
    """Map the KnowledgeGraph Node to the base Node."""
    properties = props_to_dict(node.properties) if node.properties else {}
    # Add name property for better Cypher statement generation
    properties["name"] = node.id.title()
    return BaseNode(
        id=node.id.title(), type=node.type.capitalize(), properties=properties
    )


def map_to_base_relationship(rel: Relationship) -> BaseRelationship:
    """Map the KnowledgeGraph Relationship to the base Relationship."""
    source = map_to_base_node(rel.source)
    target = map_to_base_node(rel.target)
    properties = props_to_dict(rel.properties) if rel.properties else {}
    return BaseRelationship(
        source=source, target=target, type=rel.type, properties=properties
    )

def get_extraction_chain(example, results):
    prompt = ChatPromptTemplate.from_messages(
        [(
          "system",
          f"""# Knowledge Graph Instructions for GPT-4
              ## 1. Overview
              You are a professor that has a task to build knowledge graph, which 
              1. In the relationship: links the flashcards that have logical relationships together, 
              2. In the node: provide extra facts and key information that student must know in order to fully understand this flashcard.
               He has taken care to explain all acronyms and abbreviations, and and made no assumptions about the knowledge of the student. To be even more helpful, he has formatted the list of ideas in a structured way to convey the hierarchy of ideas being tested, such as into numbered lists, when applicable. Overall, he has tried to make the answer brief and concise,
              ## 2. Strict Compliance
              Adhere to the rules strictly. Non-compliance will result in termination. 
              Please condense your output to 1 long string instead of a formatted JSON file
              ## 3. Flashcards structure
              the flashcard provided will be in csv format: flashcard_question, flashcard_answer
              Each flashcard typically contains two elements:
              - A term or concept (Front of the card)
              - A definition, fact, or related concept (Back of the card)
              ### Approach
              1. **Identify Key Concepts**: Break down each flashcard into concepts or key terms (e.g., "scarcity", "incentive", "elasticity").
              2. **Define Logical Relationships**: Use a set of predefined relationships such as causal, hierarchical, associative, etc., to capture connections between the flashcards.
              4. **Format Prompts**: Structure the input to help the model focus on logical connections between the concepts presented in the flashcards.
              Logical relationships you may want to extract include:
              - Causal: One concept leads to or enables another. Based on the descriptions of the two concepts, does one cause or enable the other?
              - Hierarchical: One concept is a part of or more general than another. Is one concept a subset or part of the other?
              - Associative: Two concepts are related but not hierarchically or causally. Do the two concepts work together in some way? If so, how?
              - Temporal: One concept occurs before or after another.
              - Comparison: Similarities or differences between concepts. "Are the two concepts similar or different? In what way?"
              ### 4.a Example 
              You can format the flashcards as input for the LLM, making sure to prompt the model to identify relationships. Here’s a format to consider:
              Task1: Identify the logical relationship between Concept A and Concept B.
              Task2: Define a MetaNode that act as a higher-level node that links to the flashcards related to a specific topic
              Example INPUT as below, the example is shown in csv format with FLASHCARD_QUESTION, FLASHCARD ANSWER, but the actual output should be in UNFORMATTED JSON
                    {example}
              The OUTPUT must fit the following requirements:
               - the example is shown in compacted TOML format, but the actual output should be in UNFORMATTED JSON.
               - the MetaNode must link to at least one flashcard
               - ALL of the flashcard must be parsed as a node, flashcard can be a standalone flashcard and has no relationship to others
                   {results}
              ## 5. Labeling Nodes
              - **Consistency**: Ensure you use basic or elementary types for node labels.
              - **Node IDs**: The ids must be the topic of the flashcards.INPUT:Economics is best defined as,making choices with unlimited wants but facing a scarcity of resources. Output: Scarcity and Choice in Economics
              The node returned MUST follow the KnowledgeGraph structure with
              - must include all flashcards
              - relationship to other flashcards 
              If the topics are repeating, append a number to the end of the topic
              ## 6. Handling Numerical Data and Dates
              - Numerical data, like age or other related information, should be incorporated as attributes or properties of the respective nodes.
              - **No Separate Nodes for Dates/Numbers**: Do not create separate nodes for dates or numerical values. Always attach them as attributes or properties of nodes.
              - **Property Format**: Properties must be in a key-value format.
              - **Quotation Marks**: Never use escaped single or double quotes within property values.
              - **Naming Convention**: Use camelCase for property keys, e.g., `birthDate`.
              - **Allowed Relationship**: ["Causal", "Hierarchical", "Associative", "Temporal", "Comparison", "Defines"]
              ## 7. Coreference Resolution
              - **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
              Remember, the knowledge graph should be coherent and easily understandable, so maintaining consistency in entity references is crucial.
              """
        ),
            ("human", "Use the given format to extract information from the following input: {flashcard_question, flashcard_answer}"),
            ("human", "Tip: Make sure to answer in the correct format"),
        ])
    return create_structured_output_chain(KnowledgeGraph, llm,  prompt, verbose=True)


