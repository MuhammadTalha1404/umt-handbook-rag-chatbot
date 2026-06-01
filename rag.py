import os
import pickle
from dotenv import load_dotenv

load_dotenv()

def load_faiss_store(faiss_path: str, pkl_path: str):
    """
    Loads a LangChain FAISS vector store from:
    - faiss_path: FAISS index file (.faiss)
    - pkl_path: metadata/docstore file (.pkl)

    Works with common LangChain save formats.
    """
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore
    from langchain_openai import OpenAIEmbeddings

    # 1) Read FAISS index
    index = faiss.read_index(faiss_path)

    # 2) Read metadata (docstore + mapping)
    with open(pkl_path, "rb") as f:
        meta = pickle.load(f)

    docstore = None
    index_to_docstore_id = None

    # Common formats across LangChain versions
    if isinstance(meta, tuple) and len(meta) == 2:
        docstore, index_to_docstore_id = meta

    elif isinstance(meta, dict):
        # sometimes keys vary by version
        docstore = meta.get("docstore") or meta.get("documents") or meta.get("docs")
        index_to_docstore_id = meta.get("index_to_docstore_id") or meta.get("index_to_id")

    if docstore is None or index_to_docstore_id is None:
        raise ValueError(
            "Could not parse the .pkl metadata. "
            "It must contain (docstore, index_to_docstore_id) or a dict with those keys."
        )

    # If docstore is a raw dict, wrap it
    if isinstance(docstore, dict):
        docstore = InMemoryDocstore(docstore)

    # 3) Embeddings MUST match what you used when building the index
    # Your index dimension is 1536, which matches text-embedding-3-small by default. :contentReference[oaicite:1]{index=1}
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 4) Build vector store object
    store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id,
    )
    return store


def retrieve(store, query: str, k: int = 4):
    # Similarity search returns Document objects with .page_content + .metadata
    return store.similarity_search(query, k=k)
