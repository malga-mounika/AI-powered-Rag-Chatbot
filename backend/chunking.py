def create_chunks(text, chunk_size=1000, overlap=200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# Test the chunking function
if __name__ == "__main__":

    text = """
    Binary search is an efficient searching algorithm.
    It works on sorted arrays.
    The time complexity of binary search is O(log n).
    """

    chunks = create_chunks(
        text,
        chunk_size=50,
        overlap=10
    )

    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(chunk)