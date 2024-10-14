import os
from langchain_openai import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Set up OpenAI key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


# Initialize the OpenAI embeddings
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
