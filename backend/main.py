from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import os
import shutil

from pypdf import PdfReader

from chunking import create_chunks
from embeddings import create_embeddings

from vector_store import (
    store_chunks,
    search_chunks,
    search_chunks_by_document,
    get_documents,
    delete_document,
    clear_documents
)

from llm import generate_answer, rewrite_question


# ==========================================
# Load environment variables
# ==========================================

load_dotenv("../.env")


# ==========================================
# FastAPI
# ==========================================

app = FastAPI()


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
    "http://localhost:5173",
    "https://ai-rag-chatbot-l9wo8j6dx-malga-mounikas-projects.vercel.app"
],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# Request Models
# ==========================================

class ChatRequest(BaseModel):

    question: str

    # Current document selected by user
    filename: str | None = None

    # Previous conversation
    history: list[dict] = Field(
        default_factory=list
    )


class SearchRequest(BaseModel):

    query: str

    top_k: int = 3

    # Optional document filter
    filename: str | None = None


# ==========================================
# Home
# ==========================================

@app.get("/")
def home():

    return {
        "message": "RAG Chatbot API is running"
    }


# ==========================================
# Health Check
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "OK"
    }


# ==========================================
# Upload PDF
# ==========================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):

    os.makedirs(
        "../documents",
        exist_ok=True
    )

    file_path = os.path.join(
        "../documents",
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return {

        "filename": file.filename,

        "message": "File uploaded successfully"
    }


# ==========================================
# Extract PDF Text
# ==========================================

@app.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...)
):

    reader = PdfReader(
        file.file
    )

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    return {

        "filename": file.filename,

        "pages": len(reader.pages),

        "text": text
    }


# ==========================================
# Chunk PDF Text
# ==========================================

@app.post("/chunk-text")
async def chunk_text(
    file: UploadFile = File(...)
):

    reader = PdfReader(
        file.file
    )

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    chunks = create_chunks(

        text,

        chunk_size=1000,

        overlap=200
    )

    return {

        "filename": file.filename,

        "total_characters": len(text),

        "total_chunks": len(chunks),

        "chunks": chunks
    }


# ==========================================
# Store Document
# ==========================================

@app.post("/store-document")
async def store_document(
    file: UploadFile = File(...)
):

    reader = PdfReader(
        file.file
    )

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"


    # --------------------------------------
    # Create chunks
    # --------------------------------------

    chunks = create_chunks(

        text,

        chunk_size=1000,

        overlap=200
    )


    # --------------------------------------
    # Create embeddings
    # --------------------------------------

    embeddings = create_embeddings(
        chunks
    )


    # --------------------------------------
    # Store in ChromaDB
    # --------------------------------------

    result = store_chunks(

        chunks,

        embeddings,

        file.filename
    )


    return {

        "filename": file.filename,

        "total_characters": len(text),

        "total_chunks": len(chunks),

        "message": result["message"]
    }


# ==========================================
# GET DOCUMENTS
# ==========================================

@app.get("/documents")
def documents():

    return get_documents()


# ==========================================
# DELETE ONE DOCUMENT
# ==========================================

@app.delete("/documents/{filename}")
def remove_document(
    filename: str
):

    result = delete_document(
        filename
    )

    return result


# ==========================================
# DELETE ALL DOCUMENTS
# ==========================================

@app.delete("/documents")
def remove_all_documents():

    result = clear_documents()

    return result


# ==========================================
# Semantic Search
# ==========================================

@app.post("/search")
async def search(
    request: SearchRequest
):

    # --------------------------------------
    # Convert question to embedding
    # --------------------------------------

    query_embedding = create_embeddings(
        [request.query]
    )[0]


    # --------------------------------------
    # Search selected document
    # --------------------------------------

    if request.filename:

        results = search_chunks_by_document(

            query_embedding,

            request.filename,

            top_k=request.top_k
        )

    else:

        results = search_chunks(

            query_embedding,

            top_k=request.top_k
        )


    documents = results.get(
        "documents",
        [[]]
    )[0]


    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]


    distances = results.get(
        "distances",
        [[]]
    )[0]


    search_results = []


    for i in range(
        len(documents)
    ):

        search_results.append({

            "rank": i + 1,

            "text": documents[i],

            "filename":
                metadatas[i]["filename"],

            "chunk_index":
                metadatas[i]["chunk_index"],

            "distance":
                distances[i]
        })


    return {

        "query": request.query,

        "filename":
            request.filename,

        "results":
            search_results
    }


# -----------------------------------
# Chat / RAG
# -----------------------------------

# -----------------------------------
# Check if question is a greeting
# -----------------------------------

def is_greeting(question: str):
    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "good morning",
        "good afternoon",
        "good evening",
        "thanks",
        "thank you"
    }

    question = question.strip().lower()

    return question in greetings


@app.post("/chat")
async def chat(request: ChatRequest):

    question = request.question.strip()

    # -----------------------------------
    # 1. Handle greetings
    # -----------------------------------

    if is_greeting(question):

        return {
            "question": question,
            "answer": "Hello! Ask me questions about your uploaded documents.",
            "sources": []
        }

    # ==========================================
    # 4. Rewrite question using conversation history
    # ==========================================

    search_question = rewrite_question(
        request.history,
        question
    )

    print(
        f"Original question: {question}"
    )

    print(
        f"Search question: {search_question}"
    )


    # ==========================================
    # 5. Create embedding from rewritten question
    # ==========================================

    question_embedding = create_embeddings(
        [search_question]
    )[0]


    # ==========================================
    # 6. Search ONLY current document
    # ==========================================

    results = search_chunks_by_document(
        question_embedding,
        request.filename,
        top_k=8
    )

    # -----------------------------------
    # 4. Get relevant document chunks
    # -----------------------------------

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    # -----------------------------------
    # 5. Check if documents were found
    # -----------------------------------

    if not documents:

        return {
            "question": question,
            "answer": "I could not find relevant information in the uploaded documents.",
            "sources": []
        }

    # -----------------------------------
    # 6. Combine retrieved chunks
    # -----------------------------------

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(
        documents
    )

    # ==========================================
    # 9. Generate Gemini answer
    # ==========================================

    answer = generate_answer(
        context,
        question,
        request.history
    )

    # -----------------------------------
    # 8. Create source information
    # -----------------------------------

    sources = []

    for i in range(len(documents)):

        sources.append({
            "filename": metadatas[i]["filename"],
            "chunk_index": metadatas[i]["chunk_index"]
        })

    # -----------------------------------
    # 9. Return answer + sources
    # -----------------------------------

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }