CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    current = []
    for word in words:
        if current and len(" ".join(current + [word])) > size:
            chunks.append(" ".join(current))
            kept = []
            for previous in reversed(current):
                if len(" ".join([previous] + kept)) > overlap:
                    break
                kept.insert(0, previous)
            current = kept
        current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks
