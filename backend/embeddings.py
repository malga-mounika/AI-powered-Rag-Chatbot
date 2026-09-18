from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    embeddings = model.encode(chunks)

    return embeddings


if __name__ == "__main__":

    text = [
        "Binary search has O(log n) time complexity.",
        "Arrays store elements in contiguous memory.",
        "Linked lists contain nodes connected by links."
    ]

    embeddings = create_embeddings(text)

    print("Number of embeddings:", len(embeddings))
    print("Embedding dimensions:", len(embeddings[0]))
    print("First embedding:")
    print(embeddings[0])