from vector_store import get_collection

TOP_K = 3


def search_policies(question, top_k=TOP_K):
    results = get_collection().query(query_texts=[question], n_results=top_k, where={"source_type": "pdf"})
    chunks = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": text, "source": metadata["source"], "page": metadata["page"]})
    return chunks
