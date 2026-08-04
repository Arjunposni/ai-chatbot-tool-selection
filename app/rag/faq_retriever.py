import os
import re
import chromadb
from chromadb.utils import embedding_functions

FAQ_PATH = "data/faq_docs.md"
COLLECTION_NAME = "healthcare_faqs"

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = chromadb.PersistentClient(path="chroma_db")


def _parse_faq_markdown(path: str) -> list[dict]:
    """
    Parses the FAQ markdown into (question, answer) chunks based on
    '## Question' headers followed by answer text.
    """
    with open(path, "r") as f:
        content = f.read()

    sections = re.split(r"\n## ", content)
    faqs = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith("# "):
            continue
        lines = section.split("\n", 1)
        question = lines[0].strip()
        answer = lines[1].strip() if len(lines) > 1 else ""
        faqs.append({"question": question, "answer": answer})
    return faqs


def build_faq_index():
    """
    Loads FAQ docs, embeds them, and stores them in a persistent Chroma collection.
    Safe to re-run — recreates the collection each time to stay in sync with the source file.
    """
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = _client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn
    )

    faqs = _parse_faq_markdown(FAQ_PATH)

    collection.add(
        documents=[f"{faq['question']} {faq['answer']}" for faq in faqs],
        metadatas=[{"question": faq["question"], "answer": faq["answer"]} for faq in faqs],
        ids=[f"faq_{i}" for i in range(len(faqs))]
    )

    print(f"Indexed {len(faqs)} FAQ entries.")
    return collection


def search_faq(query: str, min_relevance: float = 0.5) -> dict:
    """
    Searches the FAQ index for the most relevant answer to the query.
    Returns matched=False if nothing sufficiently relevant is found.
    """
    collection = _client.get_collection(COLLECTION_NAME, embedding_function=_embedding_fn)

    results = collection.query(query_texts=[query], n_results=1)

    if not results["documents"] or not results["documents"][0]:
        return {"matched": False, "answer": None, "reason": "No FAQ entries indexed"}

    distance = results["distances"][0][0]
    # Chroma returns distance (lower = more similar) for default L2/cosine space
    similarity = 1 - distance  # rough conversion, works reasonably for cosine

    if similarity < min_relevance:
        return {"matched": False, "answer": None, "reason": f"Low relevance score ({similarity:.2f})"}

    metadata = results["metadatas"][0][0]
    return {
        "matched": True,
        "question": metadata["question"],
        "answer": metadata["answer"],
        "relevance": round(similarity, 2)
    }


if __name__ == "__main__":
    build_faq_index()