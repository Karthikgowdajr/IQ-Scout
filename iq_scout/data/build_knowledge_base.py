from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
import json

load_dotenv()

print("Loading scraped data...")

igniteiq_path = "iq_scout/data/raw/igniteiq_scraped.json"
competitors_path = "iq_scout/data/raw/competitors.json"

with open(igniteiq_path, "r", encoding="utf-8") as f:
    igniteiq_data = json.load(f)

with open(competitors_path, "r", encoding="utf-8") as f:
    competitor_data = json.load(f)

all_data = igniteiq_data + competitor_data

docs = []
for item in all_data:
    docs.append(Document(
        page_content=item["content"],
        metadata={"source": item["source"]}
    ))

print(f"Loaded {len(docs)} documents")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks")

print("Creating embeddings and saving to ChromaDB...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="iq_scout/data/embeddings"
)

print(f"Knowledge base built — {len(chunks)} chunks embedded and saved")
print("Done. Ready for Phase 2.")