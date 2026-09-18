import chromadb


# -----------------------------------
# Create persistent ChromaDB database
# -----------------------------------

client = chromadb.PersistentClient(
    path="./chroma_db"
)


# -----------------------------------
# Create or get collection
# -----------------------------------

collection = client.get_or_create_collection(
    name="documents"
)


# -----------------------------------
# Store document chunks
# -----------------------------------

def store_chunks(chunks, embeddings, filename):
    """
    Store text chunks, embeddings and metadata
    in ChromaDB.
    """

    # -----------------------------------
    # Prevent duplicate document IDs
    # -----------------------------------

    # If the same PDF is uploaded again,
    # remove the old version first.
    try:
        collection.delete(
            where={
                "filename": filename
            }
        )
    except Exception:
        pass

    ids = [
        f"{filename}_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "filename": filename,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    return {
        "message": "Document stored successfully",
        "filename": filename,
        "chunks_stored": len(chunks)
    }


# -----------------------------------
# Search all documents
# -----------------------------------

def search_chunks(query_embedding, top_k=8):
    """
    Search all documents in ChromaDB.
    """

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    return results


# -----------------------------------
# Search only one document
# -----------------------------------

def search_chunks_by_document(
    query_embedding,
    filename,
    top_k=8
):
    """
    Search only the specified PDF.
    """

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=top_k,
        where={
            "filename": filename
        },
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    return results


# -----------------------------------
# Get all uploaded documents
# -----------------------------------

def get_documents():
    """
    Return all uploaded documents stored
    in ChromaDB along with chunk counts.
    """

    results = collection.get(
        include=[
            "metadatas"
        ]
    )

    metadatas = results.get(
        "metadatas",
        []
    )

    documents = {}

    for metadata in metadatas:

        if not metadata:
            continue

        filename = metadata.get(
            "filename"
        )

        if not filename:
            continue

        if filename not in documents:
            documents[filename] = 0

        documents[filename] += 1

    document_list = []

    for filename, chunk_count in documents.items():

        document_list.append({
            "filename": filename,
            "chunks": chunk_count
        })

    # Sort documents alphabetically
    document_list.sort(
        key=lambda x: x["filename"].lower()
    )

    return {
        "count": len(document_list),
        "documents": document_list
    }


# -----------------------------------
# Get one document
# -----------------------------------

def get_document(filename):
    """
    Get information about one specific PDF.
    """

    results = collection.get(
        where={
            "filename": filename
        },
        include=[
            "metadatas"
        ]
    )

    metadatas = results.get(
        "metadatas",
        []
    )

    if not metadatas:
        return None

    return {
        "filename": filename,
        "chunks": len(metadatas)
    }


# -----------------------------------
# Delete one document
# -----------------------------------

def delete_document(filename):
    """
    Delete all chunks belonging
    to one PDF.
    """

    collection.delete(
        where={
            "filename": filename
        }
    )

    return {
        "message": "Document deleted successfully",
        "filename": filename
    }


# -----------------------------------
# Delete all documents
# -----------------------------------

def clear_documents():
    """
    Delete all stored documents.
    """

    global collection

    client.delete_collection(
        name="documents"
    )

    collection = client.get_or_create_collection(
        name="documents"
    )

    return {
        "message": "All documents cleared"
    }