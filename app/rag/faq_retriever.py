import re
import chromadb
from chromadb.utils import embedding_functions

FAQ_PATH = "data/faq_docs.md"
COLLECTION_NAME = "healthcare_faqs"

_client = chromadb.PersistentClient(path="chroma_db")

_embedding_fn = None




def get_embedding_function():
    """
    Lazily initialize the embedding model.
    The model is only loaded the first time it is needed.
    """

    global _embedding_fn

    if _embedding_fn is None:
        _embedding_fn = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

    return _embedding_fn


def _parse_faq_markdown(path: str) -> list[dict]:
    """
    Parses the FAQ markdown into question/answer chunks.
    """

    with open(path, "r", encoding="utf-8") as f:
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

        faqs.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    return faqs


def build_faq_index():
    """
    Creates (or recreates) the Chroma FAQ collection.
    Safe to run multiple times.
    """

    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = _client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    faqs = _parse_faq_markdown(FAQ_PATH)

    collection.add(
        documents=[
            f"{faq['question']} {faq['answer']}"
            for faq in faqs
        ],
        metadatas=[
            {
                "question": faq["question"],
                "answer": faq["answer"],
            }
            for faq in faqs
        ],
        ids=[
            f"faq_{i}"
            for i in range(len(faqs))
        ],
    )

    print(f"Indexed {len(faqs)} FAQ entries.")

    return collection


def search_faq(
    query: str,
    min_relevance: float = 0.5,
) -> dict:
    """
    Searches the FAQ collection for the
    most relevant answer.
    """

    collection = _client.get_collection(
        COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
    embedding_fn = get_embedding_function()

    query_embedding = embedding_fn([query])[0]

    print("\n" + "=" * 80)
    print("QUERY VECTOR EMBEDDING")
    print("=" * 80)

    print("QUERY:")
    print(query)

    print("\nMODEL:")
    print("all-MiniLM-L6-v2")

    print("\nVECTOR DIMENSIONS:")
    print(len(query_embedding))

    print("\nVECTOR:")
    print(query_embedding)

    print("=" * 80)

    results = collection.query(
        query_texts=[query],
        n_results=1,
    )

    if (
        not results["documents"]
        or not results["documents"][0]
    ):
        return {
            "matched": False,
            "answer": None,
            "reason": "No FAQ entries indexed",
        }

    distance = results["distances"][0][0]

    similarity = 1 - distance

    if similarity < min_relevance:
        return {
            "matched": False,
            "answer": None,
            "reason": (
                f"Low relevance score "
                f"({similarity:.2f})"
            ),
        }

    metadata = results["metadatas"][0][0]

    return {
        "matched": True,
        "question": metadata["question"],
        "answer": metadata["answer"],
        "relevance": round(
            similarity,
            2,
        ),
    }


if __name__ == "__main__":
    build_faq_index()