#Reads the source for response and convert them into vectors

import os
import glob
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
MAX_BATCH_SIZE = 5000

def load_data():
    client = chromadb.PersistentClient(path = DB_PATH)

    collection_name = "support_corpus"

    try:
        client.delete_collection(collection_name)
    except:
        pass

    collection = client.create_collection(name = collection_name)

    md_files = glob.glob(os.path.join(DATA_DIR, "**", "*.md"), recursive=True)

    documents = []
    metadatas = []
    ids = []
    count = 0

    for file_path in md_files:
        relative_path = os.path.relpath(file_path, DATA_DIR)
        product_tag = relative_path.split(os.sep)[0]

        with open(file_path, 'r', encoding = 'utf-8') as f:
            content = f.read()

            chunks = [content[i:i+1000] for i in range(0, len(content), 800)]

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": relative_path,
                    "company": product_tag,
                    "chunk_id": i
                })
                ids.append(f"doc_{count}_{i}")
        count += 1

        if count % 50 == 0:
            print(f"Processed {count} files...")

    for i in range(0, len(documents), MAX_BATCH_SIZE):
        end_idx = min(i + MAX_BATCH_SIZE, len(documents))
        collection.add(
            documents = documents[i:end_idx],
            metadatas = metadatas[i:end_idx],
            ids = ids[i:end_idx]
        )

if __name__ == "__main__":
    load_data()