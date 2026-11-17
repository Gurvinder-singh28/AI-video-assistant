import uuid

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"


class OnnxEmbeddings(Embeddings):
    """Same all-MiniLM-L6-v2 model, but runs on onnxruntime: no torch, low memory."""

    def __init__(self):
        self._fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts):
        return [[float(x) for x in vec] for vec in self._fn(list(texts))]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OnnxEmbeddings()
    return _embeddings


def build_vector_store(transcript: str) -> Chroma:
    print("Building vector store", flush=True)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    return Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=f"{COLLECTION_NAME}_{uuid.uuid4().hex[:8]}",
        persist_directory=CHROMA_DIR,
    )


def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})