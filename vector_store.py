from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

CHROMA_FOLDER = Path("chroma_db")
COLLECTION_NAME = "enterprise_rag"
BATCH_SIZE = 500

embedding_function = DefaultEmbeddingFunction()


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_FOLDER))
    return client.get_or_create_collection(COLLECTION_NAME, embedding_function=embedding_function)


def replace_chunks(source, chunks):
    collection = get_collection()
    collection.delete(where={"source": source})
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        collection.add(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[chunk["metadata"] for chunk in batch],
        )
