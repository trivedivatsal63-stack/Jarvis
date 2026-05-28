import os
import re
import datetime

CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "jarvis_memories"

chroma_available = True

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chroma_available = False

_chroma_client = None
_collection = None
_model = None
_embeddings_available = False
_embeddings_checked = False


def _get_model():
    global _model, _embeddings_available, _embeddings_checked
    if _embeddings_checked:
        return _model
    _embeddings_checked = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _embeddings_available = True
    except Exception:
        _model = None
        _embeddings_available = False
    return _model


def _get_embeddings(texts):
    model = _get_model()
    if model is None:
        return None
    try:
        return model.encode(texts, show_progress_bar=False).tolist()
    except Exception:
        return None


def embeddings_available():
    return _get_model() is not None


def get_collection():
    global _chroma_client, _collection
    if not chroma_available:
        return None
    if _collection is not None:
        return _collection
    try:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        return _collection
    except Exception:
        return None


def init_vector_memory():
    collection = get_collection()
    if collection is not None:
        count = collection.count()
        return count
    return 0


def store_memory(session_id, summary, topics, timestamp=None):
    if not chroma_db_available() or not summary:
        return False
    collection = get_collection()
    if collection is None:
        return False
    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()
    text = f"{summary} topics: {topics}"
    emb = _get_embeddings([text])
    if emb is None:
        return False
    try:
        import uuid
        doc_id = str(uuid.uuid4())
        collection.add(
            embeddings=emb,
            documents=[summary],
            metadatas=[{
                "session_id": session_id,
                "timestamp": timestamp,
                "topics": topics,
            }],
            ids=[doc_id],
        )
        return True
    except Exception:
        return False


def query_memories(query, n_results=5):
    if not chroma_db_available():
        return []
    collection = get_collection()
    if collection is None:
        return []
    emb = _get_embeddings([query])
    if emb is None:
        return []
    try:
        import numpy as np
        results = collection.query(
            query_embeddings=emb,
            n_results=min(n_results, collection.count() or 1),
        )
        output = []
        if results and results.get("ids") and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                output.append({
                    "summary": results["documents"][0][i] if results.get("documents") else "",
                    "session_id": meta.get("session_id", ""),
                    "topics": meta.get("topics", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "distance": float(results["distances"][0][i]) if results.get("distances") else 0.0,
                })
        return output
    except Exception:
        return []


def summarize_conversation(messages):
    if not messages:
        return ""
    text_parts = []
    char_limit = 2000
    total = 0
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        line = f"{role}: {content}"
        if total + len(line) > char_limit:
            allowed = char_limit - total
            if allowed > 0:
                text_parts.append(line[:allowed])
            break
        text_parts.append(line)
        total += len(line)
    combined = " ".join(text_parts)
    sentences = re.split(r'(?<=[.!?])\s+', combined)
    summary_sentences = []
    for msg in messages:
        content = msg.get("content", "")
        first_sent = re.split(r'(?<=[.!?])\s+', content.strip())[0] if content.strip() else ""
        if first_sent and len(first_sent) > 10:
            summary_sentences.append(first_sent)
    if not summary_sentences:
        return combined[:500]
    return " ".join(summary_sentences)


def store_conversation(session_id, messages):
    if not messages:
        return False
    summary = summarize_conversation(messages)
    if not summary:
        return False
    all_text = " ".join(m.get("content", "") for m in messages)
    words = re.findall(r'[a-zA-Z]+', all_text.lower())
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "shall", "can",
                 "to", "of", "in", "for", "on", "with", "at", "by", "from",
                 "as", "into", "through", "during", "before", "after", "above",
                 "below", "between", "out", "off", "over", "under", "again",
                 "further", "then", "once", "here", "there", "when", "where",
                 "why", "how", "all", "each", "every", "both", "few", "more",
                 "most", "other", "some", "such", "no", "nor", "not", "only",
                 "own", "same", "so", "than", "too", "very", "just", "because",
                 "and", "but", "or", "if", "while", "that", "this", "these",
                 "those", "it", "its", "you", "your", "i", "me", "my", "we",
                 "our", "he", "him", "his", "she", "her", "they", "them",
                 "their", "what", "which", "who", "whom", "about", "up"}
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    topics = ", ".join(w for w, _ in sorted_words[:8])
    if not topics:
        topics = "general"
    return store_memory(session_id, summary, topics)


def get_relevant_context(user_message, n_results=3):
    if not chroma_db_available():
        return ""
    results = query_memories(user_message, n_results=n_results)
    if not results:
        return ""
    lines = ["Relevant past conversations:"]
    for r in results:
        lines.append(f"- {r['summary']} (topics: {r['topics']})")
    return "\n".join(lines)


def chroma_db_available():
    return chroma_available and _embeddings_available
